import click,json
#import binascii,socket,struct
import socketserver,socket,logging,logging.config,binascii
from hyperdns.netdns.query import DNSRecord

class DNSHandler(socketserver.BaseRequestHandler):
    """
        Handler for socketserver. Transparently handles both TCP/UDP requests
        (TCP requests have length prepended) and hands off lookup to resolver
        instance specified in <SocketServer>.resolver 
    """

    udplen = 0                  # Max udp packet length (0 = ignore)

    def handle(self):
        if self.server.socket_type == socket.SOCK_STREAM:
            self.protocol = 'tcp'
            data = self.request.recv(8192)
            length = struct.unpack("!H",bytes(data[:2]))[0]
            while len(data) - 2 < length:
                data += self.request.recv(8192)
            data = data[2:]
        else:
            self.protocol = 'udp'
            data,connection = self.request

        logging.debug("Received: [%s:%d] (%s) <%d> : %s" % (
                    self.client_address[0],
                    self.client_address[1],
                    self.protocol,
                    len(data),
                    binascii.hexlify(data)))

        try:
            rdata = self.get_reply(data)
            self.server.logger.log_send(self,rdata)

            if self.protocol == 'tcp':
                rdata = struct.pack("!H",len(rdata)) + rdata
                self.request.sendall(rdata)
            else:
                connection.sendto(rdata,self.client_address)

        except Exception as e:
            logging.error(e)

    def get_reply(self,data):
        request = DNSRecord.parse(data)
        self.server.logger.log_request(self,request)

        resolver = self.server.resolver
        reply = resolver.resolve(request,self)
        self.server.logger.log_reply(self,reply)

        if self.protocol == 'udp':
            rdata = reply.pack()
            if self.udplen and len(rdata) > self.udplen:
                truncated_reply = reply.truncate()
                rdata = truncated_reply.pack()
                self.server.logger.log_truncated(self,truncated_reply)
        else:
            rdata = reply.pack()

        return rdata
          
@click.command()
@click.pass_context
def serve(ctx,**kwargs):
    """Start a server on port 15353
    """
    address=""
    port=15353
    #logging.config.dictConfig(lconfig)
    logging.basicConfig()
    server = socketserver.UDPServer((address,port),DNSHandler)
    # set allow_reuse_addr
    server.serve_forever()



class BaseResolver(object):
    """
        Base resolver implementation. Provides 'resolve' method which is
        called by DNSHandler with the decode request (DNSRecord instance) 
        and returns a DNSRecord instance as reply.

        In most cases you should be able to create a custom resolver by
        just replacing the resolve method with appropriate resolver code for
        application (see fixedresolver/zoneresolver/shellresolver for
        examples)

        Note that a single instance is used by all DNSHandler instances so 
        need to consider blocking & thread safety.
    """
    def resolve(self,request,handler):
        """
            Example resolver - respond to all requests with NXDOMAIN
        """
        reply = request.reply()
        reply.header.rcode = getattr(RCODE,'NXDOMAIN')
        return reply



class DNSLogger:

    """
        The class provides a default set of logging functions for the various
        stages of the request handled by a DNSServer instance which are
        enabled/disabled by flags in the 'log' class variable.

        To customise logging create an object which implements the DNSLogger
        interface and pass instance to DNSServer.

        The methods which the logger instance must implement are:

            log_recv          - Raw packet received
            log_send          - Raw packet sent
            log_request       - DNS Request
            log_reply         - DNS Response
            log_truncated     - Truncated
            log_error         - Decoding error
            log_data          - Dump full request/response
    """

    def __init__(self,log="",prefix=True):
        """
            Selectively enable log hooks depending on log argument
            (comma separated list of hooks to enable/disable)

            - If empty enable default log hooks
            - If entry starts with '+' (eg. +send,+recv) enable hook
            - If entry starts with '-' (eg. -data) disable hook
            - If entry doesn't start with +/- replace defaults

            Prefix argument enables/disables log prefix
        """
        default = ["request","reply","truncated","error"]
        log = log.split(",") if log else []
        enabled = set([ s for s in log if s[0] not in '+-'] or default)
        [ enabled.add(l[1:]) for l in log if l.startswith('+') ]
        [ enabled.discard(l[1:]) for l in log if l.startswith('-') ]
        for l in ['log_recv','log_send','log_request','log_reply',
                  'log_truncated','log_error','log_data']:
            if l[4:] not in enabled:
                setattr(self,l,self.log_pass)
        self.prefix = prefix

    def log_pass(self,*args):
        pass

    def log_prefix(self,handler):
        if self.prefix:
            return "%s [%s:%s] " % (time.strftime("%Y-%M-%d %X"),
                               handler.__class__.__name__,
                               handler.server.resolver.__class__.__name__)
        else:
            return ""

    def log_recv(self,handler,data):
        print("%sReceived: [%s:%d] (%s) <%d> : %s" % (
                    self.log_prefix(handler),
                    handler.client_address[0],
                    handler.client_address[1],
                    handler.protocol,
                    len(data),
                    binascii.hexlify(data)))

    def log_send(self,handler,data):
        print("%sSent: [%s:%d] (%s) <%d> : %s" % (
                    self.log_prefix(handler),
                    handler.client_address[0],
                    handler.client_address[1],
                    handler.protocol,
                    len(data),
                    binascii.hexlify(data)))

    def log_request(self,handler,request):
        print("%sRequest: [%s:%d] (%s) / '%s' (%s)" % (
                    self.log_prefix(handler),
                    handler.client_address[0],
                    handler.client_address[1],
                    handler.protocol,
                    request.q.qname,
                    QTYPE[request.q.qtype]))
        self.log_data(request)

    def log_reply(self,handler,reply):
        print("%sReply: [%s:%d] (%s) / '%s' (%s) / RRs: %s" % (
                    self.log_prefix(handler),
                    handler.client_address[0],
                    handler.client_address[1],
                    handler.protocol,
                    reply.q.qname,
                    QTYPE[reply.q.qtype],
                    ",".join([QTYPE[a.rtype] for a in reply.rr])))
        self.log_data(reply)

    def log_truncated(self,handler,reply):
        print("%sTruncated Reply: [%s:%d] (%s) / '%s' (%s) / RRs: %s" % (
                    self.log_prefix(handler),
                    handler.client_address[0],
                    handler.client_address[1],
                    handler.protocol,
                    reply.q.qname,
                    QTYPE[reply.q.qtype],
                    ",".join([QTYPE[a.rtype] for a in reply.rr])))
        self.log_data(reply)

    def log_error(self,handler,e):
        print("%sInvalid Request: [%s:%d] (%s) :: %s" % (
                    self.log_prefix(handler),
                    handler.client_address[0],
                    handler.client_address[1],
                    handler.protocol,
                    e))

    def log_data(self,dnsobj):
        print("\n",dnsobj.toZone("    "),"\n",sep="")




class ProxyResolver(BaseResolver):
    """
        Proxy resolver - passes all requests to upstream DNS server and
        returns response

        Note that the request/response will be each be decoded/re-encoded 
        twice:

        a) Request packet received by DNSHandler and parsed into DNSRecord 
        b) DNSRecord passed to ProxyResolver, serialised back into packet 
           and sent to upstream DNS server
        c) Upstream DNS server returns response packet which is parsed into
           DNSRecord
        d) ProxyResolver returns DNSRecord to DNSHandler which re-serialises
           this into packet and returns to client

        In practice this is actually fairly useful for testing but for a
        'real' transparent proxy option the DNSHandler logic needs to be
        modified (see PassthroughDNSHandler)

    """

    def __init__(self,address,port):
        self.address = address
        self.port = port

    def resolve(self,request,handler):
        if handler.protocol == 'udp':
            proxy_r = request.send(self.address,self.port)
        else:
            proxy_r = request.send(self.address,self.port,tcp=True)
        reply = DNSRecord.parse(proxy_r)
        return reply

class PassthroughDNSHandler(DNSHandler):
    """
        Modify DNSHandler logic (get_reply method) to send directly to 
        upstream DNS server rather then decoding/encoding packet and
        passing to Resolver (The request/response packets are still
        parsed and logged but this is not inline)
    """
    def get_reply(self,data):
        host,port = self.server.resolver.address,self.server.resolver.port

        request = DNSRecord.parse(data)
        self.log_request(request)

        if self.protocol == 'tcp':
            data = struct.pack("!H",len(data)) + data
            response = send_tcp(data,host,port)
            response = response[2:]
        else:
            response = send_udp(data,host,port)

        reply = DNSRecord.parse(response)
        self.log_reply(reply)

        return response

def send_tcp(data,host,port):
    """
        Helper function to send/receive DNS TCP request
        (in/out packets will have prepended TCP length header)
    """
    sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    sock.connect((host,port))
    sock.sendall(data)
    response = sock.recv(8192)
    length = struct.unpack("!H",bytes(response[:2]))[0]
    while len(response) - 2 < length:
        response += sock.recv(8192)
    sock.close()
    return response

def send_udp(data,host,port):
    """
        Helper function to send/receive DNS UDP request
    """
    sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    sock.sendto(data,(host,port))
    response,server = sock.recvfrom(8192)
    sock.close()
    return response

if __name__ == '__main__':

    import argparse,sys,time

    p = argparse.ArgumentParser(description="DNS Proxy")
    p.add_argument("--port","-p",type=int,default=53,
                    metavar="<port>",
                    help="Local proxy port (default:53)")
    p.add_argument("--address","-a",default="",
                    metavar="<address>",
                    help="Local proxy listen address (default:all)")
    p.add_argument("--upstream","-u",default="8.8.8.8:53",
            metavar="<dns server:port>",
                    help="Upstream DNS server:port (default:8.8.8.8:53)")
    p.add_argument("--tcp",action='store_true',default=False,
                    help="TCP proxy (default: UDP only)")
    p.add_argument("--passthrough",action='store_true',default=False,
                    help="Dont decode/re-encode request/response (default: off)")
    p.add_argument("--log",default="request,reply,truncated,error",
                    help="Log hooks to enable (default: +request,+reply,+truncated,+error,-recv,-send,-data)")
    p.add_argument("--log-prefix",action='store_true',default=False,
                    help="Log prefix (timestamp/handler/resolver) (default: False)")
    args = p.parse_args()

    args.dns,_,args.dns_port = args.upstream.partition(':')
    args.dns_port = int(args.dns_port or 53)

    print("Starting Proxy Resolver (%s:%d -> %s:%d) [%s]" % (
                        args.address or "*",args.port,
                        args.dns,args.dns_port,
                        "UDP/TCP" if args.tcp else "UDP"))

    resolver = ProxyResolver(args.dns,args.dns_port)
    handler = PassthroughDNSHandler if args.passthrough else DNSHandler
    logger = DNSLogger(args.log,args.log_prefix)
    udp_server = DNSServer(resolver,
                           port=args.port,
                           address=args.address,
                           logger=logger,
                           handler=handler)
    udp_server.start_thread()

    if args.tcp:
        tcp_server = DNSServer(resolver,
                               port=args.port,
                               address=args.address,
                               tcp=True,
                               logger=logger,
                               handler=handler)
        tcp_server.start_thread()

    while udp_server.isAlive():
        time.sleep(1)


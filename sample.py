from hyperdns.netdns import dotify

def split(fqdn,zone):
    f=dotify(fqdn)
    z=dotify(zone)
    if f.endswith(z):
        return (f[:-len(z)-1],z)
    return (None,None)

print(split('abc.def.com','def.com.'))

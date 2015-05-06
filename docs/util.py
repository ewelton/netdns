from hyperdns.netdns import (
    RecordSpec
)
import ipaddress

# Examples of record specs
spec = RecordSpec.a_record('1.2.3.4',255)
print(spec)

spec = RecordSpec.a_record(ipaddress.IPv4Address('1.2.3.4'))
print(spec)

spec = RecordSpec.a_record('1.2.3.4',ttl = "5m")
print(spec)

spec = RecordSpec.aaaa_record('FE80:0000:0000:0000:0202:B3FF:FE1E:8329')
print(spec)

spec = RecordSpec.mx_record('mail.example.com',22)
print(spec)
print(spec.mx_priority)
print(spec.mx_exchange)


spec = RecordSpec.a_record('1.2.3.4')
print(spec.rdtype)
print(spec.rdtype.value)
print(spec.rdtype.name)

spec = RecordSpec.a_record('1.2.3.4')
print(spec.rdclass)
print(spec.rdclass.value)
print(spec.rdclass.name)


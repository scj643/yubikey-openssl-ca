# Overview
This repo documents how to use a Yubikey as a root CA with domain constraints to limit issuing certs.
Using environment variables is not recommended. It is only done here for demonstration purposes.

## Package Requirements
### `yubico-piv-tool`
Needed for the `libykcs11.so.2` library

### `ykman`
Needed to manage the pin, puk, and management key

# gen\_permitted.py
This script takes a list of domains and generate the name constraint list for you.
## Example
`$ python3 gen_permitted.py example.org example.com`

```
permitted;DNS.0=example.org
permitted;DNS.1=example.com

permitted;URI.0=example.org
permitted;URI.1=.example.org
permitted;URI.2=example.com
permitted;URI.3=.example.com

permitted;email.0=example.org
permitted;email.1=.example.org
permitted;email.2=example.com
permitted;email.3=.example.com
```

# Directory Setup
```sh
mkdir certs crl csr db public private
chmod 700 private
touch db/index
openssl rand -hex 16  > db/serial
echo 1001 > db/crlnumber
```

# Yubikey
## Demo environment variables
For demo purposes we have the Yubikey Pin stored in a file called `yk-vars` and use the default pins
```
YK_MANAGEMENT=[GENERATED MANAGEMENT KEY]
YK_PIN=123456
YK_PUK=12345678
SSL_O="Demo"
SSL_C="US"
```
## Set PIN and PUK Retries (Optional)
This will reset the pin to default
`ykman piv access set-retries 10 5`

## Generate Management Key and Require Touch
`ykman piv access change-management-key -a AES256 -g -t`

## Set PIN
`ykman piv access change-pin -P 123456`

## Set PUK
`ykman piv access change-puk -p 12345678`

## Enable all keys for PKCS11
(Yubico's docs are not correct for object import since it doesn't convert the hex string to binary)
`echo -n C10114C20100FE00 | xxd -r -p > /tmp/yk_all_objects`
`ykman piv objects import 0x5FC10C /tmp/yk_all_objects`
### One liner with environment variables
`echo -n C10114C20100FE00 | xxd -r -p | ykman piv objects import 0x5FC10C - -P $YK_PIN  -m $YK_MANAGEMENT`

## Generate key and write public key to `public/root.pem`
`ykman piv keys generate -a ECCP384 -F pem --pin-policy ALWAYS --touch-policy ALWAYS 9c -m $YK_MANAGEMENT -P $YK_PIN public/root.pem`

# Root certificate
## CA Setup
### Notes
You may need to change the line `MODULE_PATH` in the `pkcs11_section` of `root.cnf` depending on your OS

### CSR
`openssl req -new -config root.cnf -engine pkcs11 -keyform engine -key "pkcs11:object=Private key for Digital Signature;type=private"  -out csr/root.csr`

### Self Sign
`openssl ca -selfsign -config root.cnf -in csr/root.csr -out certs/root.crt -extensions ca_ext -keyform engine -engine pkcs11`

### Import x509 to Yubikey
`ykman piv certificates import -m $YK_MANAGEMENT -P $YK_PIN 9c certs/root.crt`

## CRL
### Generate CRL
`openssl ca -config root.cnf -keyform engine -engine pkcs11 -gencrl -out crl/root.crl -cert certs/root.crt`

## OCSP Cert
### Generate EC Params
`openssl genpkey -genparam -algorithm ec -pkeyopt ec_paramgen_curve:secp384r1 -out ECPARAM.pem`

### Generate EC Key and CSR
`openssl req -new -config root.cnf -newkey ec:ECPARAM.pem -subj "/C=$SSL_C/O=$SSL_O/CN=OCSP Root Responder" -keyout private/root-ocsp.key -out root-ocsp.csr`

### Create OCSP Cert
Optional and this cert can not be revoked.
`openssl ca -config root.cnf -keyform engine -engine pkcs11 -in root-ocsp.csr -out root-ocsp.crt -extensions ocsp_ext -days 365`

# Notes
## p11-tool
Using p11-tool requires telling it to use the libykcs11.so.2 library.
`alias p11tool-yk="p11tool --provider /usr/lib64/libykcs11.so.2"`
# References
[Openssl Cookbook: Creating a Root CA](https://www.feistyduck.com/library/openssl-cookbook/online/openssl-command-line/private-ca-creating-root.html)  
[Smallstep: Build a Tiny Certificate Authority For Your Homelab](https://smallstep.com/blog/build-a-tiny-ca-with-raspberry-pi-yubikey/)  
[Yubico: Certificate Authority with a YubiKey](https://developers.yubico.com/PIV/Guides/Certificate_authority.html)  
## Allowing Retired Management keys
[Retired PIV Slots Unavailable When Accessing via PKCS11](https://support.yubico.com/hc/en-us/articles/4585159896220-Troubleshooting-Retired-PIV-Slots-Unavailable-When-Accessing-via-PKCS11)  
## http://cedric.dufour.name
[Yubikey PIV Info](http://cedric.dufour.name/blah/IT/YubiKeyHowto.html)  
[General PKCS11 Info](http://cedric.dufour.name/blah/IT/SmartCardsHowto.html)  

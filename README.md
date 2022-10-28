# Overview
This repo documents how to use a Yubikey as a root CA with domain constraints to limit issuing certs.

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

# Yubikey
## Demo environment variables
For demo purposes we have the Yubikey Pin stored in a file called `yk-vars` and use the default pins
```
YK_MANAGEMENT=[GENERATED MANAGEMENT KEY]
YK_PIN=123456
YK_PUK=12345678
SSL_O="Test CA"
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

## Generate key and write public key to stdout
`ykman piv keys generate -a ECCP384 -F pem --pin-policy ALWAYS --touch-policy ALWAYS 9c -`

# Root certificate
## Directory Setup
```sh
mkdir certs db private
chmod 700 private
touch db/index
openssl rand -hex 16  > db/serial
echo 1001 > db/crlnumber
```

## CA Setup
### Notes
You may need to change the line `MODULE_PATH` in the `pkcs11_section` of `root.cnf` depending on your OS

### CSR
`openssl req -new -config root.cnf -engine pkcs11 -keyform engine -key "pkcs11:object=Private key for Digital Signature;type=private"  -out ca.csr`

### Self Sign
`openssl ca -selfsign -config root.cnf -in ca.csr -out ca.crt -extensions ca_ext -keyform engine -engine pkcs11`

## CRL
### Generate CRL
`openssl ca -config root.cnf -keyform engine -engine pkcs11 -gencrl -out root.crl -cert certs/CA_SERIAL.pem`

## OCSP Cert
### Generate EC Params
`openssl genpkey -genparam -algorithm ec -pkeyopt ec_paramgen_curve:secp384r1 -out ECPARAM.pem`

### Generate EC Key and CSR
`openssl req -new -config root.cnf -newkey ec:ECPARAM.pem -subj "/C=$SSL_C/O=$SSL_O/CN=OCSP Root Responder" -keyout private/root-ocsp.key -out root-ocsp.csr`

### Create OCSP Cert
Optional and this cert can not be revoked.
`openssl ca -config root.cnf -keyform engine -engine pkcs11 -in root-ocsp.csr -out root-ocsp.crt -extensions ocsp_ext -days 365`

# References
[Openssl Cookbook: Creating a Root CA](https://www.feistyduck.com/library/openssl-cookbook/online/openssl-command-line/private-ca-creating-root.html)  
[Smallstep: Build a Tiny Certificate Authority For Your Homelab](https://smallstep.com/blog/build-a-tiny-ca-with-raspberry-pi-yubikey/)  
[Yubico: Certificate Authority with a YubiKey](https://developers.yubico.com/PIV/Guides/Certificate_authority.html)  
## http://cedric.dufour.name
[Yubikey PIV Info](http://cedric.dufour.name/blah/IT/YubiKeyHowto.html)  
[General PKCS11 Info](http://cedric.dufour.name/blah/IT/SmartCardsHowto.html)  

##################################################################
# Copyright 2018 CBSD Project Authors. All Rights Reserved.
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License
#################################################################

#################################################################
# Readme file for installing and configuring OCSP Responder (server) for X.509 RSA certificates for test labs for FCC part 96 testing of CBSD UUT and Domain Proxy UUT
# Version 1.0 28-June-2018
# Idan Raz iraz@airspan.com
##################################################################

###################################################################
# OCSP Responder running on Fedora-Workstation-Live-x86_64-28-1.1 with ocspd.x86_64 1.9.0-13.fc28
# X.509 certificate generation Used with OpenSSL openssl-1.0.1e-57.el6.x86_64 on CentOS 6.9 x86_64 kernel 2.6.32-696.16.1.el6.x86_64
# According to document "readme_file_x509_RSA_certs_test_labs" Version 1.4 28-April-2018 which is part of WInnForum software Test Harness for CBSD, v1.0.0.2 24-May-2018 available on https://github.com/Wireless-Innovation-Forum/Citizens-Broadband-Radio-Service-Device/releases   
#
# opensslcbrs1.cnf is part of WInnForum software Test Harness for CBSD, v1.0.0.2 24-May-2018 available on https://github.com/Wireless-Innovation-Forum/Citizens-Broadband-Radio-Service-Device/releases
# ocspopensslcbrs1.cnf is the modified file from opensslcbrs1.cnf to be used for this Readme file with regards to OCSP Responder
# Modifications are
#   1) adding new extension sections for OCSP Responder X.509 certificate [ ocsp_responder_cert ]    
###################################################################

###################################################################
# It is possible for debug purposes to run OCSP Responder using OpenSSL commands, but this has limited capabilities and some issues (exiting on OCSP malformed Request, not handling properly X.509 certificate chains)
# Hence the choice for OCSP Responder running on Fedora-Workstation-Live-x86_64-28-1.1 with ocspd.x86_64 1.9.0-13.fc28
###################################################################

###################################################################
# Actions for OCSP Responder the test lab needs to do:
#   1) Download Fedora-Workstation-Live-x86_64-28-1.1.iso for Linux from https://getfedora.org/en/workstation/download/
#   2) Install Fedora-Workstation-Live-x86_64-28-1.1
#   3) Install ocspd.x86_64 1.9.0-13.fc28 
#   4) Execute the steps described in "readme_file_x509_RSA_certs_test_labs" Version 1.4 28-April-2018
#   5) Generate X.509 certificate for OCSP Responder
#   6) Configure OCSP Responder parameters 
#   7) Activate OCSP Responder on Fedora-Workstation-Live-x86_64-28-1.1
################################################################### 

########################################################################
# All files generated using the openssl commands below are in PEM format
# file name convention: private key file name has <file name>.key  , CSR (Certificate Signing Request) file name has <file name>.csr   , certificate file name has <file name>.pem  
#########################################################################  

########################################################################
# The machine running the openssl commands must be synchronized UTC time (for example via NTP)
# this is so the X.509 generated certificates will have correct validity timestamps
# Before starting the X.509 certificate generation verify your machine with openssl is showing correct and accurate Date and Time Of Day   
#########################################################################  

########################################################################
# The machine running the OCSP Responder must be synchronized UTC time (for example via NTP)
# Before starting the OCSP Responder verify your Fedora-Workstation machine is showing correct and accurate Date and Time Of Day   
#########################################################################  

###################################################################
# OpenSSL commands used for X.509 RSA certificate generation:
# 1) generate RSA private key. <key size> is 2048 bit or 4096 bit :
# openssl genrsa -out <private key file name> <key size>      
# 
# 2) create CSR (Certificate Signing Request)associated with the private key : 
# openssl req -new -key <private key file name> -out <CSR file name> -config <openssl.cnf file to use> 
#
# 3) signing a CSR with a CA certificate :   
# openssl x509 -req -in <CSR file name> -CA <file name of CA certificate signing the CSR> -CAkey <private key of the CA certificate signing the CSR> -CAcreateserial -out <certificate file name> -days <number of days for certificate validity> <-sha256 OR -sha384> -extfile <openssl.cnf file to use> -extensions <extension section to use in the openssl.cnf file to use>
#           
# 4) verify certificate parameters :
# openssl x509 -in <certificate file name> -text -noout
###################################################################

###################################################################
# First action for test lab is to download the Fedora-Workstation iso file
###################################################################   

Step 1) Download Fedora-Workstation-Live-x86_64-28-1.1.iso for Linux from https://getfedora.org/en/workstation/download/

###################################################################
# Second action for test lab is to install Fedora-Workstation
###################################################################   

Step 2) Install Fedora-Workstation-Live-x86_64-28-1.1 on a machine

###################################################################
# Third action for test lab is to install ocspd.x86_64 1.9.0-13.fc28 on the Fedora-Workstation machine
###################################################################   

Step 3) on the Fedora-Workstation machine open a terminal

Step 4) verify root credentials (typically done by the "sudo bash" command in the terminal)

Step 5) install the following packages using the yum method in the following order: (Fedora-Workstation machine requires internet connection for this step)

yum install vsftpd
yum install pki-ca
yum install pki-console
yum install pki-ocsp
yum install ocspd

###################################################################
# Fourth action for test lab is to execute the steps described in "readme_file_x509_RSA_certs_test_labs" Version 1.4 28-April-2018
###################################################################   

Step 6) Execute the steps described in "readme_file_x509_RSA_certs_test_labs" Version 1.4 28-April-2018 (if not already executed)

###################################################################
the following X.509 certificates are needed for continuing to the next steps of this Readme file:
SAS Provider CA (file name sascacert.pem) with its private key (file name sascapriv.key)
Certificate Revocation List issued by the SAS Provider CA (file name crlserver.crl)
###################################################################

###################################################################
# Fifth action for test lab is to generate X.509 certificate for OCSP Responder 
###################################################################   

Step 7) generate RSA private key for OCSP Responder certificate  

openssl genrsa -out ocspresponderpriv.key 2048

Step 8) generate a CSR for OCSP Responder certificate

openssl req -new -key ocspresponderpriv.key -out ocsprespondercsr.csr -config /home/ocspopensslcbrs1.cnf

You are about to be asked to enter information that will be incorporated
into your certificate request.
What you are about to enter is what is called a Distinguished Name or a DN.
There are quite a few fields but you can leave some blank
For some fields there will be a default value,
If you enter '.', the field will be left blank.
-----
Country Name (2 letter code) [XX]:US
Organization Name (eg, company) [Default Company Ltd]:Airspan Networks
Organizational Unit Name (eg, section) []:Airspan Networks Inter Operability Lab
Common Name (eg, your name or your server's hostname) []:ocsp.testharness.cbrstestlab.com

Please enter the following 'extra' attributes
to be sent with your certificate request
A challenge password []:

Step 9) sign the CSR of OCSP Responder certificate with SAS Provider CA

openssl x509 -req -in ocsprespondercsr.csr -CA sascacert.pem -CAkey sascapriv.key -out ocsprespondercert.pem -days 180 -sha256 -extfile /home/ocspopensslcbrs1.cnf -extensions ocsp_responder_cert

Step 10) verify OCSP Responder certificate parameters

openssl x509 -in ocsprespondercert.pem -text -noout

Certificate:
    Data:
        Version: 3 (0x2)
        Serial Number: 10177691706620776706 (0x8d3e6caef6921102)
    Signature Algorithm: sha256WithRSAEncryption
        Issuer: C=US, O=Airspan Networks, OU=RSA SAS Provider CA9001, CN=WInnForum RSA SAS Provider CA
        Validity
            Not Before: Jun 25 13:41:13 2018 GMT
            Not After : Dec 22 13:41:13 2018 GMT
        Subject: C=US, O=Airspan Networks, OU=Airspan Networks Inter Operability Lab, CN=ocsp.testharness.cbrstestlab.com
        Subject Public Key Info:
            Public Key Algorithm: rsaEncryption
                Public-Key: (2048 bit)
                Modulus:
                    00:ea:0b:c0:fb:7b:93:80:df:f2:d1:9d:48:83:f9:
                    06:62:b7:e6:a5:1b:9a:65:67:62:42:d5:33:ba:e9:
                    d1:20:c5:8b:a9:0d:5e:2e:ce:ea:c0:e0:c3:5d:32:
                    dd:f5:d3:72:ec:16:6e:dd:ee:9f:27:a6:1b:f2:03:
                    39:5b:ca:34:87:5a:67:c1:32:d4:1d:31:5f:46:97:
                    bd:b8:31:be:84:11:4f:29:8c:f2:14:5f:a9:d8:cc:
                    ae:38:69:87:72:fd:e5:ae:f5:40:36:50:40:fc:be:
                    27:b8:49:94:4b:c2:7e:03:ec:42:16:02:74:4c:40:
                    96:c0:94:25:ac:69:73:8d:02:e5:fb:4c:31:05:8d:
                    c4:be:a6:0c:b1:63:61:73:41:8b:75:50:1f:e6:47:
                    52:d7:b1:fd:15:f8:9e:d0:93:97:bd:fd:2e:0d:62:
                    57:35:5b:b6:22:a7:46:c6:91:70:54:cb:ff:b5:06:
                    a1:b6:a0:67:fb:77:b7:25:54:8b:b9:3d:e1:59:f0:
                    17:a1:39:e0:b2:1a:36:72:99:99:42:4a:6a:0c:21:
                    26:e2:52:14:2b:03:57:48:e4:01:99:32:18:36:30:
                    b5:04:4e:3c:d1:4a:95:9a:84:93:6d:a7:26:67:d3:
                    ba:6f:28:fc:c8:e6:27:73:b6:11:5e:69:9d:72:8b:
                    d4:09
                Exponent: 65537 (0x10001)
        X509v3 extensions:
            X509v3 Subject Key Identifier:
                CF:82:C4:DF:69:AF:0D:DB:4E:75:C6:D5:78:56:5B:FF:2D:46:D1:00
            X509v3 Authority Key Identifier:
                keyid:E9:88:B4:B7:6C:39:CD:1B:9A:30:18:14:B6:2B:BA:15:6D:20:AA:95

            X509v3 Key Usage: critical
                Digital Signature, Key Encipherment
            X509v3 Extended Key Usage:
                OCSP Signing
    Signature Algorithm: sha256WithRSAEncryption
         77:63:1a:b0:32:8d:a7:9a:cf:dd:ad:ca:47:70:16:df:e0:81:
         91:cd:31:a6:01:81:ce:d0:6a:4e:da:ba:18:87:f4:0c:ca:de:
         c9:33:15:ea:21:be:d9:d6:73:ce:24:fc:0f:da:3b:d7:97:a4:
         b2:88:4a:6a:d3:0d:de:f3:a0:3e:52:19:5e:e0:12:f8:86:26:
         2a:76:f2:e7:82:c9:46:69:d1:1d:2a:b6:ac:f2:66:1a:c9:32:
         01:94:38:75:b4:67:28:c1:26:95:f6:35:44:ba:9b:bc:4f:c9:
         3d:c0:b8:3a:73:b3:62:01:08:64:a7:a9:df:87:05:77:fc:52:
         48:e1:dc:99:63:c2:9e:3b:6c:62:2a:37:3b:3c:b6:05:22:32:
         a0:80:fb:81:3a:05:e0:73:e9:00:5e:7f:e0:b6:2e:bf:90:5a:
         15:26:09:91:74:1b:c0:54:56:df:a9:12:da:8f:fc:75:08:3d:
         21:f8:52:35:2f:16:1e:20:97:e6:89:7d:7c:f0:23:41:e2:66:
         7a:05:83:d8:a6:3b:d7:58:d1:05:f6:20:37:ac:82:94:52:63:
         5c:51:83:02:ef:4a:85:ea:31:09:ac:f7:7b:30:d7:b9:1a:86:
         6e:aa:3f:25:f3:c9:39:ba:ef:0b:dc:36:2c:58:3e:00:58:0f:
         77:17:c8:f3:59:71:78:75:32:e5:e4:90:1b:08:5c:38:48:bb:
         8d:9c:ab:9b:c8:bd:d1:b1:31:27:1d:0d:81:51:4d:f0:b4:1c:
         5c:d9:15:4f:f9:66:fd:98:e0:77:7d:e3:54:78:73:94:8c:7d:
         ca:47:9a:3a:60:e6:58:c3:a9:cb:d9:58:12:fb:6e:93:ee:f2:
         e7:0f:a9:09:4b:b0:18:2e:a6:93:9f:6c:e1:bb:61:0a:3d:b7:
         49:3d:c4:87:07:ce:80:b2:be:8f:53:45:49:89:dd:7c:56:a0:
         16:52:82:b7:06:56:ce:1a:69:89:e0:1f:da:8c:12:68:0f:6a:
         ef:45:d1:25:c1:c0:2e:4f:b5:37:03:31:d4:14:f0:7f:42:5c:
         d4:cc:92:5b:c1:09:95:fc:8f:d8:12:30:b2:79:06:3c:37:f1:
         a7:9a:17:a4:81:61:7a:9d:84:38:07:9c:dd:c6:f0:1d:ce:1e:
         30:04:e0:80:87:49:45:6c:3e:b3:f9:22:aa:90:78:b9:4e:9c:
         05:61:42:fc:e1:51:51:2c:f4:2d:6f:bf:00:f5:27:37:e0:d3:
         8b:e7:9a:a1:29:0a:ef:b6:38:3f:52:62:0b:1a:03:dc:1b:2c:
         c0:50:8d:2f:d0:71:be:63:ea:77:80:fe:4f:fa:b5:f4:b8:ad:
         df:9a:00:86:54:f5:23:c8

###################################################################
Verify the X.509 OCSP Responder certificate includes the following:
1) CN=ocsp.testharness.cbrstestlab.com (Common Name matching the URI of the OCSP Responder in the SAS Provider certificate with CRL extensions) 
2) X509v3 Extended Key Usage: OCSP Signing
###################################################################

###################################################################
# Sixth action for test lab is to configure OCSP Responder parameters 
###################################################################   

Step 11) on the Fedora-Workstation machine open a terminal

Step 12) verify root credentials (typically done by the "sudo bash" command in the terminal)

Step 13) use vi to edit the file /etc/ocspd/ocspd.conf for the following:

# Port where the server will listen for incoming requests.
port		 	= 80

# crl_url = ldap://ldap.server.org:389
crl_url = file:///etc/ocspd/crls/crl3.pem

Step 14) verify the existing directory of ocspd private key is empty 

ls -l /etc/ocspd/private  

Step 15) place the OCSP Responder private key from previous steps (file name ocspresponderpriv.key) in the existing directory /etc/ocspd/private

Step 16) copy the OCSP Responder private key to a new file name to match the configuration of the ocspd.conf file

cp /etc/ocspd/private/ocspresponderpriv.key  /etc/ocspd/private/ocspd_key.pem   
   
Step 17) verify the existing directory of ocspd certificate is empty 

ls -l /etc/ocspd/certs  

Step 18) place the OCSP Responder X.509 certificate from previous steps (file name ocsprespondercert.pem) in the existing directory /etc/ocspd/certs

Step 19) copy the OCSP Responder X.509 certificate to a new file name to match the configuration of the ocspd.conf file

cp /etc/ocspd/certs/ocsprespondercert.pem  /etc/ocspd/certs/ocspd_cert.pem

Step 20) place the SAS Provider CA from previous steps (file name sascacert.pem) in the existing directory /etc/ocspd/certs

Step 21) copy the SAS Provider CA to a new file name to match the PKI chain configuration of the ocspd.conf file

cp /etc/ocspd/certs/sascacert.pem  /etc/ocspd/certs/chain_certs.pem

Step 22) copy the SAS Provider CA to a new file name to match the CA configuration of the ocspd.conf file

cp /etc/ocspd/certs/sascacert.pem  /etc/ocspd/certs/1st_cacert.pem

###################################################################
# The ocspd.x86_64 1.9.0-13.fc28 on the Fedora-Workstation machine requires the direct CA certificate that signed the OCSP Responder X.509 certificate and the Certificate Revocation List
# This direct CA certificate is the SAS Provider CA (file name sascacert.pem) according to the steps described in "readme_file_x509_RSA_certs_test_labs" Version 1.4 28-April-2018
# The ocspd.x86_64 1.9.0-13.fc28 on the Fedora-Workstation machine does not require the CBRS Root CA which signed the SAS Provider CA  
###################################################################   

Step 23) verify the existing directory of ocspd certificate revocation list is empty 

ls -l /etc/ocspd/crls  

Step 24) place the Certificate Revocation List from previous steps (file name crlserver.crl) in the existing directory /etc/ocspd/crls

Step 25) copy the Certificate Revocation List to a new file name to match the configuration of the ocspd.conf file

cp /etc/ocspd/crls/crlserver.crl /etc/ocspd/crls/crl_01.pem

Step 26) copy the Certificate Revocation List to a new file name to match the modified configuration of the ocspd.conf file executed in previous steps:

cp /etc/ocspd/crls/crlserver.crl /etc/ocspd/crls/crl3.pem

###################################################################
# Seventh action for test lab is to Activate OCSP Responder on Fedora-Workstation 
###################################################################   

Step 27) on the Fedora-Workstation machine open a terminal

Step 28) verify root credentials (typically done by the "sudo bash" command in the terminal)

Step 29) stop the firewall of the Fedora-Workstation

systemctl stop firewalld

Step 30) disable the firewall of the Fedora-Workstation

systemctl disable firewalld

Step 31) verify the firewall of the Fedora-Workstation is disabled and not running

systemctl status firewalld

firewalld.service - firewalld - dynamic firewall daemon
   Loaded: loaded (/usr/lib/systemd/system/firewalld.service; disabled; vendor preset: enabled)
   Active: inactive (dead)

Step 32) verify the HTTP Server of the Fedora-Workstation is disabled and not running

systemctl status httpd

httpd.service - The Apache HTTP Server
   Loaded: loaded (/usr/lib/systemd/system/httpd.service; disabled; vendor preset: disabled)
   Active: inactive (dead)

###################################################################
# since ocspd on the Fedora-Workstation is also configured to run on port 80, verify that the httpd which has default port 80 is not running
# this is to avoid potential conflicts on the Fedora-Workstation  
###################################################################   

Step 33) verify the ocspd of the Fedora-Workstation is disabled and not running

systemctl status ocspd

ocspd.service - OpenCA OCSP Responder
   Loaded: loaded (/usr/lib/systemd/system/ocspd.service; disabled; vendor preset: disabled)
   Active: inactive (dead)

Step 34) activate the ocspd of the Fedora-Workstation

systemctl start ocspd

Step 35) verify the ocspd of the Fedora-Workstation is active and running properly

systemctl status ocspd

ocspd.service - OpenCA OCSP Responder
   Loaded: loaded (/usr/lib/systemd/system/ocspd.service; disabled; vendor preset: disabled)
   Active: active (running) since Wed 2018-06-27 17:21:39 IDT; 5s ago
  Process: 18813 ExecStart=/usr/sbin/ocspd -d -c /etc/ocspd/ocspd.conf $OPTIONS (code=exited, status=0/SUCCESS)
 Main PID: 18814 (ocspd)
    Tasks: 151 (limit: 4915)
   Memory: 6.5M
   CGroup: /system.slice/ocspd.service
           └─18814 /usr/sbin/ocspd -d -c /etc/ocspd/ocspd.conf

Jun 27 17:21:39 ocsp-testharness-cbrstestlab-com systemd[1]: Starting OpenCA OCSP Responder...
Jun 27 17:21:39 ocsp-testharness-cbrstestlab-com ocspd[18813]: OpenCA OCSPD v1.9.0 - starting.
Jun 27 17:21:39 ocsp-testharness-cbrstestlab-com ocspd[18813]: CRL loaded for first_ca
Jun 27 17:21:39 ocsp-testharness-cbrstestlab-com systemd[1]: Started OpenCA OCSP Responder.

###################################################################
# At this point the OCSP Responder is up and waiting for OCSP Requests from CBSD/Domain Proxy UUT
# The OCSP Response will be signed by the OCSP Responder X.509 certificate generated in the previous steps
# The OCSP Response will include SAS Provider CA so CBSD/Domain Proxy UUT can verify the OCSP Responder PKI Chain (the CBRS Root CA resides on the CBSD/Domain Proxy UUT according to the steps described in "readme_file_x509_RSA_certs_test_labs" Version 1.4 28-April-2018)
# The OCSP Response for the queried X.509 certificate is according to the Certificate Revocation List:
# 1) if the queried X.509 certificate is not included in the Certificate Revocation List then OCSP Response will have "certStatus: good"
# 2) if the queried X.509 certificate is included in the Certificate Revocation List then OCSP Response will have "certStatus: revoked"
###################################################################   

######################################################################################################################
######################################################################################################################
######################################################################################################################
# Below is ocspopensslcbrs1.cnf to use by test lab for generating the OCSP Responder X.509 certificate 

##################################################################
# Copyright 2018 CBSD Project Authors. All Rights Reserved.
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License
#################################################################
# OpenSSL configuration file for OCSP Responder X.509 RSA certificate for test labs for CBRS FCC part 96 testing
# used with openssl-1.0.1e-57.el6.x86_64
# Version 1.0 28-June-2018
# Idan Raz iraz@airspan.com
##################################################################

# This definition stops the following lines choking if HOME isn't
# defined.
HOME			= .
RANDFILE		= $ENV::HOME/.rnd

# Extra OBJECT IDENTIFIER info:
#oid_file		= $ENV::HOME/.oid
oid_section		= new_oids

# To use this configuration file with the "-extfile" option of the
# "openssl x509" utility, name here the section containing the
# X.509v3 extensions to use:
# extensions		= 
# (Alternatively, use a configuration file that has only
# X.509v3 extensions in its main [= default] section.)

[ new_oids ]

# We can add new OIDs in here for use by 'ca', 'req' and 'ts'.
# Add a simple OID like this:
# testoid1=1.2.3.4
# Or use config file substitution like this:
# testoid2=${testoid1}.5.6

# Policies used by the TSA examples.
tsa_policy1 = 1.2.3.4.1
tsa_policy2 = 1.2.3.4.5.6
tsa_policy3 = 1.2.3.4.5.7

####################################################################
[ ca ]
default_ca	= CA_default		# The default ca section

####################################################################
[ CA_default ]

dir		= /etc/pki/CA		# Where everything is kept
certs		= $dir/certs		# Where the issued certs are kept
crl_dir		= $dir/crl		# Where the issued crl are kept
database	= $dir/index.txt	# database index file.
#unique_subject	= no			# Set to 'no' to allow creation of
					# several ctificates with same subject.
new_certs_dir	= $dir/newcerts		# default place for new certs.

certificate	= $dir/cacert.pem 	# The CA certificate
serial		= $dir/serial 		# The current serial number
crlnumber	= $dir/crlnumber	# the current crl number
					# must be commented out to leave a V1 CRL
crl		= $dir/crl.pem 		# The current CRL
private_key	= $dir/private/cakey.pem# The private key
RANDFILE	= $dir/private/.rand	# private random number file

x509_extensions	= usr_cert		# The extentions to add to the cert

# Comment out the following two lines for the "traditional"
# (and highly broken) format.
name_opt 	= ca_default		# Subject Name options
cert_opt 	= ca_default		# Certificate field options

# Extension copying option: use with caution.
# copy_extensions = copy

# Extensions to add to a CRL. Note: Netscape communicator chokes on V2 CRLs
# so this is commented out by default to leave a V1 CRL.
# crlnumber must also be commented out to leave a V1 CRL.
# crl_extensions	= crl_ext

default_days	= 365			# how long to certify for
default_crl_days= 30			# how long before next CRL
default_md	= default		# use public key default MD
preserve	= no			# keep passed DN ordering

# A few difference way of specifying how similar the request should look
# For type CA, the listed attributes must be the same, and the optional
# and supplied fields are just that :-)
policy		= policy_match

# For the CA policy
[ policy_match ]
countryName		= match
stateOrProvinceName	= optional
organizationName	= match
organizationalUnitName	= optional
commonName		= supplied
emailAddress		= optional

# For the 'anything' policy
# At this point in time, you must list all acceptable 'object'
# types.
[ policy_anything ]
countryName		= optional
stateOrProvinceName	= optional
localityName		= optional
organizationName	= optional
organizationalUnitName	= optional
commonName		= supplied
emailAddress		= optional

####################################################################
[ req ]
default_bits		= 2048
default_md		= sha384
default_keyfile 	= privkey.pem
distinguished_name	= req_distinguished_name
attributes		= req_attributes
x509_extensions	= v3_ca	# The extentions to add to the self signed cert

# Passwords for private keys if not present they will be prompted for
# input_password = secret
# output_password = secret

# This sets a mask for permitted string types. There are several options. 
# default: PrintableString, T61String, BMPString.
# pkix	 : PrintableString, BMPString (PKIX recommendation before 2004)
# utf8only: only UTF8Strings (PKIX recommendation after 2004).
# nombstr : PrintableString, T61String (no BMPStrings or UTF8Strings).
# MASK:XXXX a literal mask value.
# WARNING: ancient versions of Netscape crash on BMPStrings or UTF8Strings.
string_mask = utf8only

# req_extensions = v3_req # The extensions to add to a certificate request

[ req_distinguished_name ]
countryName			= Country Name (2 letter code)
countryName_default		= XX
countryName_min			= 2
countryName_max			= 2

#stateOrProvinceName		= State or Province Name (full name)
#stateOrProvinceName_default	= Default Province

#localityName			= Locality Name (eg, city)
#localityName_default	= Default City

0.organizationName		= Organization Name (eg, company)
0.organizationName_default	= Default Company Ltd

# we can do this but it is not needed normally :-)
#1.organizationName		= Second Organization Name (eg, company)
#1.organizationName_default	= World Wide Web Pty Ltd

organizationalUnitName		= Organizational Unit Name (eg, section)
#organizationalUnitName_default	=

commonName			= Common Name (eg, your name or your server\'s hostname)
commonName_max			= 64

#emailAddress			= Email Address
#emailAddress_max		= 64

# SET-ex3			= SET extension number 3

[ req_attributes ]
challengePassword		= A challenge password
challengePassword_min		= 4
challengePassword_max		= 20

#unstructuredName		= An optional company name

[ usr_cert ]

# These extensions are added when 'ca' signs a request.

# This goes against PKIX guidelines but some CAs do it and some software
# requires this to avoid interpreting an end user certificate as a CA.

basicConstraints=CA:FALSE

# Here are some examples of the usage of nsCertType. If it is omitted
# the certificate can be used for anything *except* object signing.

# This is OK for an SSL server.
# nsCertType			= server

# For an object signing certificate this would be used.
# nsCertType = objsign

# For normal client use this is typical
# nsCertType = client, email

# and for everything including object signing:
# nsCertType = client, email, objsign

# This is typical in keyUsage for a client certificate.
# keyUsage = nonRepudiation, digitalSignature, keyEncipherment

# This will be displayed in Netscape's comment listbox.
nsComment			= "OpenSSL Generated Certificate"

# PKIX recommendations harmless if included in all certificates.
subjectKeyIdentifier=hash
authorityKeyIdentifier=keyid,issuer

# This stuff is for subjectAltName and issuerAltname.
# Import the email address.
# subjectAltName=email:copy
# An alternative to produce certificates that aren't
# deprecated according to PKIX.
# subjectAltName=email:move

# Copy subject details
# issuerAltName=issuer:copy

#nsCaRevocationUrl		= http://www.domain.dom/ca-crl.pem
#nsBaseUrl
#nsRevocationUrl
#nsRenewalUrl
#nsCaPolicyUrl
#nsSslServerName

# This is required for TSA certificates.
# extendedKeyUsage = critical,timeStamping

[ v3_req ]

# Extensions to add to a certificate request

basicConstraints = CA:FALSE
keyUsage = nonRepudiation, digitalSignature, keyEncipherment

[ v3_ca ]


# Extensions for a typical CA


# PKIX recommendation.

subjectKeyIdentifier=hash

authorityKeyIdentifier=keyid:always,issuer

# This is what PKIX recommends but some broken software chokes on critical
# extensions.
#basicConstraints = critical,CA:true
# So we do this instead.
basicConstraints = critical, CA:true

# Key usage: this is typical for a CA certificate. However since it will
# prevent it being used as an test self-signed certificate it is best
# left out by default.
keyUsage = critical, cRLSign, keyCertSign

# Some might want this also
# nsCertType = sslCA, emailCA

# Include email address in subject alt name: another PKIX recommendation
# subjectAltName=email:copy
# Copy issuer details
# issuerAltName=issuer:copy

# DER hex encoding of an extension: beware experts only!
# obj=DER:02:03
# Where 'obj' is a standard or added object
# You can even override a supported extension:
# basicConstraints= critical, DER:30:03:01:01:FF
################################################

[ cbrs_domain_proxy_ca ]

subjectKeyIdentifier=hash
authorityKeyIdentifier=keyid:always,issuer
basicConstraints = critical, CA:true
keyUsage = critical, cRLSign, keyCertSign
certificatePolicies = 1.3.6.1.4.1.46609.2.1, 1.3.6.1.4.1.46609.1.1.5
subjectAltName = DNS:domainproxyca.testharness.cbsd.winnf.github.com

####################################################################

[ cbrs_sas_ca ]

subjectKeyIdentifier=hash
authorityKeyIdentifier=keyid:always,issuer
basicConstraints = critical, CA:true
keyUsage = critical, cRLSign, keyCertSign
certificatePolicies = 1.3.6.1.4.1.46609.2.1, 1.3.6.1.4.1.46609.1.1.5
subjectAltName = DNS:sasproivderca.testharness.cbsd.winnf.github.com 

#####################################################################

[ cbrs_cbsd_mfr_ca ]

subjectKeyIdentifier=hash
authorityKeyIdentifier=keyid:always,issuer
basicConstraints = critical, CA:true, pathlen:1
keyUsage = critical, cRLSign, keyCertSign
certificatePolicies = 1.3.6.1.4.1.46609.2.1, 1.3.6.1.4.1.46609.1.1.5
subjectAltName = DNS:cbsdmfrca.testharness.cbsd.winnf.github.com

####################################################################

[ professional_installer_ca ]

subjectKeyIdentifier=hash
authorityKeyIdentifier=keyid:always,issuer
basicConstraints = critical, CA:true
keyUsage = critical, cRLSign, keyCertSign
certificatePolicies = 1.3.6.1.4.1.46609.2.1, 1.3.6.1.4.1.46609.1.1.5
subjectAltName = DNS:professionalinstallerca.testharness.cbsd.winnf.github.com

######################################################################

[ sas_cert ]

subjectKeyIdentifier = hash
authorityKeyIdentifier = keyid:always,issuer
keyUsage = critical, digitalSignature, keyEncipherment
certificatePolicies = 1.3.6.1.4.1.46609.2.1, 1.3.6.1.4.1.46609.1.1.1
subjectAltName = DNS:asil-iot14.airspan.com, otherName:1.3.6.1.4.1.46609.1.6;UTF8:MockSAS FRN

######################################################################

[ sas_cert_with_crl ]

subjectKeyIdentifier = hash
authorityKeyIdentifier = keyid:always,issuer
keyUsage = critical, digitalSignature, keyEncipherment
certificatePolicies = 1.3.6.1.4.1.46609.2.1, 1.3.6.1.4.1.46609.1.1.1
subjectAltName = DNS:testharness.ver1002.cbrstestlab.com, otherName:1.3.6.1.4.1.46609.1.6;UTF8:MockSAS FRN
authorityInfoAccess = OCSP;URI:http://ocsp.testharness.cbrstestlab.com
crlDistributionPoints=URI:http://crlserver.testharness.cbrstestlab.com/crlserver.crl

######################################################################

[ cbsd_cert ]

subjectKeyIdentifier = hash
authorityKeyIdentifier = keyid:always,issuer
keyUsage = critical, digitalSignature, keyEncipherment 
certificatePolicies = 1.3.6.1.4.1.46609.2.1, 1.3.6.1.4.1.46609.1.1.3
subjectAltName = otherName:1.3.6.1.4.1.46609.1.4;UTF8:FCC ID CBSD UUT,otherName:1.3.6.1.4.1.46609.1.5;UTF8:Serial CBSD UUT


######################################################################

[ domain_proxy_cert ]

subjectKeyIdentifier = hash
authorityKeyIdentifier = keyid:always,issuer
keyUsage = critical, digitalSignature, keyEncipherment
certificatePolicies = 1.3.6.1.4.1.46609.2.1, 1.3.6.1.4.1.46609.1.1.4
subjectAltName = otherName:1.3.6.1.4.1.46609.1.6;UTF8:Domain Proxy UUT FRN

#####################################################################

[ cpi_cert ]

subjectKeyIdentifier = hash
authorityKeyIdentifier = keyid:always,issuer
keyUsage = critical, digitalSignature, keyEncipherment
certificatePolicies = 1.3.6.1.4.1.46609.2.1, 1.3.6.1.4.1.46609.1.1.2
subjectAltName = otherName:1.3.6.1.4.1.46609.1.7;UTF8:CPI

####################################################################

[ ocsp_responder_cert ]

subjectKeyIdentifier = hash
authorityKeyIdentifier = keyid:always,issuer
keyUsage = critical, digitalSignature, keyEncipherment
extendedKeyUsage = OCSPSigning
 
####################################################################
[ crl_ext ]

# CRL extensions.
# Only issuerAltName and authorityKeyIdentifier make any sense in a CRL.

# issuerAltName=issuer:copy
authorityKeyIdentifier=keyid:always

[ proxy_cert_ext ]
# These extensions should be added when creating a proxy certificate

# This goes against PKIX guidelines but some CAs do it and some software
# requires this to avoid interpreting an end user certificate as a CA.

basicConstraints=CA:FALSE

# Here are some examples of the usage of nsCertType. If it is omitted
# the certificate can be used for anything *except* object signing.

# This is OK for an SSL server.
# nsCertType			= server

# For an object signing certificate this would be used.
# nsCertType = objsign

# For normal client use this is typical
# nsCertType = client, email

# and for everything including object signing:
# nsCertType = client, email, objsign

# This is typical in keyUsage for a client certificate.
# keyUsage = nonRepudiation, digitalSignature, keyEncipherment

# This will be displayed in Netscape's comment listbox.
nsComment			= "OpenSSL Generated Certificate"

# PKIX recommendations harmless if included in all certificates.
subjectKeyIdentifier=hash
authorityKeyIdentifier=keyid,issuer

# This stuff is for subjectAltName and issuerAltname.
# Import the email address.
# subjectAltName=email:copy
# An alternative to produce certificates that aren't
# deprecated according to PKIX.
# subjectAltName=email:move

# Copy subject details
# issuerAltName=issuer:copy

#nsCaRevocationUrl		= http://www.domain.dom/ca-crl.pem
#nsBaseUrl
#nsRevocationUrl
#nsRenewalUrl
#nsCaPolicyUrl
#nsSslServerName

# This really needs to be in place for it to be a proxy certificate.
proxyCertInfo=critical,language:id-ppl-anyLanguage,pathlen:3,policy:foo

####################################################################
[ tsa ]

default_tsa = tsa_config1	# the default TSA section

[ tsa_config1 ]

# These are used by the TSA reply generation only.
dir		= ./demoCA		# TSA root directory
serial		= $dir/tsaserial	# The current serial number (mandatory)
crypto_device	= builtin		# OpenSSL engine to use for signing
signer_cert	= $dir/tsacert.pem 	# The TSA signing certificate
					# (optional)
certs		= $dir/cacert.pem	# Certificate chain to include in reply
					# (optional)
signer_key	= $dir/private/tsakey.pem # The TSA private key (optional)

default_policy	= tsa_policy1		# Policy if request did not specify it
					# (optional)
other_policies	= tsa_policy2, tsa_policy3	# acceptable policies (optional)
digests		= md5, sha1		# Acceptable message digests (mandatory)
accuracy	= secs:1, millisecs:500, microsecs:100	# (optional)
clock_precision_digits  = 0	# number of digits after dot. (optional)
ordering		= yes	# Is ordering defined for timestamps?
				# (optional, default: no)
tsa_name		= yes	# Must the TSA name be included in the reply?
				# (optional, default: no)
ess_cert_id_chain	= no	# Must the ESS cert id chain be included?
				# (optional, default: no)



		 

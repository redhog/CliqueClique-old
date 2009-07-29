from M2Crypto import BIO, Rand, SMIME, X509
import StringIO

# Make a MemoryBuffer of the message.
# buf = BIO.MemoryBuffer('a sign of our times')


buf = BIO.File(open("inputfile.txt"))

# Seed the PRNG.
#Rand.load_file('/dev/random', 1024)

# Instantiate an SMIME object; set it up; sign the buffer.
s = SMIME.SMIME()
s.load_key_bio(BIO.File(open('signer.key.pem')), BIO.File(open('signer.pem')))
p7 = s.sign(buf, SMIME.PKCS7_DETACHED)

out = BIO.MemoryBuffer()
p7.write(out)

x509 = X509.load_cert('signer.pem')
sk = X509.X509_Stack()
sk.push(x509)
s.set_x509_stack(sk)
    
st = X509.X509_Store()
st.load_info('signer.pem')
s.set_x509_store(st)

p7 = SMIME.load_pkcs7_bio(out)

v = s.verify(p7, BIO.File(open("inputfile.txt")))
print "VERIFY", v

import io
from werkzeug.formparser import MultiPartParser
for payload in [b'a',b'abc\r',b'abc\n',b'abc\r\n']:
 body=b'--BOUNDARY\r\nContent-Disposition: form-data; name="f"; filename="x"\r\n\r\n'+payload+b'\r\n--BOUNDARY--\r\n'
 for size in [1,2,3,65536]:
  _,files=MultiPartParser(buffer_size=size).parse(io.BytesIO(body),b'BOUNDARY',len(body))
  print(repr(payload),size,repr(files['f'].read()))

# PMC ID Converter Client

This is a simple Python wrapper around the PMC ID converter service.

### Example Usage

```python
from pmc_id_conv_client import PMCIDConverter, IDConvRequest, IDConvResult

converter = PMCIDConverter(email='<your-email>')
ids = ['PMC7611378']
req = IDConvRequest(ids=ids)
res_list = converter.convert_ids(req)
for r in res_list:
    print(r)
```



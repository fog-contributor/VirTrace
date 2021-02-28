# VirTrace

What need to do:

1. There is <b>no possibility</b> for ECMP  - use only first hop match route. <b>For future upgrades.</b>
2. There is <b>no checking</b> for VRRP dependiencies on first-hop router interface (which router actually will be send packets).<b>For future upgrades.</b>
3. There is <b>no possibilities</b> for working with VRFs. <b>For future upgrades.</b>
4. There is <b>no possibilities</b> for working with other vendors (only Huawei). <b>For future upgrades.</b>
5. There is no web-interface for input IP-addresses (at this time this feature in development with Django)
6. All code staff that actually you see - <b>need to be well organized</b> (functions and so on). For nowadays - it's "spagetti code"

Virttrace now looks as follows:

at the browser - http://127.0.0.1:5000/index.html

<image> </image>

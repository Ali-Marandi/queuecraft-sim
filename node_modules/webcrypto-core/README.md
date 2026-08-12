<h1 align="center">
  webcrypto-core
</h1>

<div align="center">

![NPM License](https://img.shields.io/npm/l/webcrypto-core)
![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/PeculiarVentures/webcrypto-core/test.yml?label=test)
[![npm version](https://img.shields.io/npm/v/webcrypto-core.svg)](https://www.npmjs.com/package/webcrypto-core)
![Coveralls](https://img.shields.io/coverallsCoverage/github/PeculiarVentures/webcrypto-core)
[![npm downloads](https://img.shields.io/npm/dm/webcrypto-core.svg)](https://www.npmjs.com/package/webcrypto-core)

</div>

We have created a number of WebCrypto polyfills including: [node-webcrypto-ossl](https://github.com/PeculiarVentures/node-webcrypto-ossl), [node-webcrypto-p11](https://github.com/PeculiarVentures/node-webcrypto-p11), and [webcrypto-liner](https://github.com/PeculiarVentures/webcrypto-liner).  `webcrypto-core` was designed to be a common layer to be used by all of these libraries for input validation.

Unless you intend to create a WebCrypto polyfill this library is probably not useful to you.

## Installing

```
npm install webcrypto-core
```

## Example

Current examples shows how you can implement your own WebCrypt interface

```js
const core = require(".");
const crypto = require("crypto");

class Sha1Provider extends core.ProviderCrypto {

  constructor() {
    super();

    this.name = "SHA-1";
    this.usages = [];
  }

  async onDigest(algorithm, data) {
    const hash = crypto.createHash("SHA1").update(Buffer.from(data)).digest();
    return new Uint8Array(hash).buffer;
  }

}

class SubtleCrypto extends core.SubtleCrypto {
  constructor() {
    super();

    // Add SHA1 provider to SubtleCrypto
    this.providers.set(new Sha1Provider());
  }
}

class Crypto extends core.Crypto {

  constructor() {
    this.subtle = new SubtleCrypto();
  }

  getRandomValues(array) {
    const buffer = Buffer.from(array.buffer);
    crypto.randomFillSync(buffer);
    return array;
  }

}

const webcrypto = new Crypto();
webcrypto.subtle.digest("SHA-1", Buffer.from("TEST MESSAGE"))
  .then((hash) => {
    console.log(Buffer.from(hash).toString("hex")); // dbca505deb07e1612d944a69c0c851f79f3a4a60
  })
  .catch((err) => {
    console.error(err);
  });
```
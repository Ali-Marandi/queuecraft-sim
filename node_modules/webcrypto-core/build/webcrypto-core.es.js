/**
 * Copyright (c) 2019-2026, Peculiar Ventures
 * SPDX-License-Identifier: MIT
 */

import * as bytes from '@peculiar/utils/bytes';
import * as encoding from '@peculiar/utils/encoding';
import { AsnProp, AsnPropTypes, AsnType, AsnTypeTypes, AsnIntegerConverter, AsnSerializer, AsnConvert } from '@peculiar/asn1-schema';
import { __decorate } from 'tslib';
import { JsonProp, JsonPropTypes } from '@peculiar/json-schema';
import * as asn1 from 'asn1js';
export { BufferSourceConverter } from '@peculiar/utils/legacy';

class CryptoError extends Error {
}

class AlgorithmError extends CryptoError {
}

class UnsupportedOperationError extends CryptoError {
    constructor(methodName) {
        super(`Unsupported operation: ${methodName ? `${methodName}` : ""}`);
    }
}

class OperationError extends CryptoError {
}

class RequiredPropertyError extends CryptoError {
    constructor(propName) {
        super(`${propName}: Missing required property`);
    }
}

class PemConverter {
    static toArrayBuffer(pem) {
        const base64 = pem
            .replace(/-{5}(BEGIN|END) .*-{5}/g, "")
            .replace("\r", "")
            .replace("\n", "");
        return bytes.toArrayBuffer(encoding.base64.decode(base64));
    }
    static toUint8Array(pem) {
        const bytes = this.toArrayBuffer(pem);
        return new Uint8Array(bytes);
    }
    static fromBufferSource(buffer, tag) {
        const base64 = encoding.base64.encode(buffer);
        let sliced;
        let offset = 0;
        const rows = [];
        while (offset < base64.length) {
            sliced = base64.slice(offset, offset + 64);
            if (sliced.length) {
                rows.push(sliced);
            }
            else {
                break;
            }
            offset += 64;
        }
        const upperCaseTag = tag.toUpperCase();
        return `-----BEGIN ${upperCaseTag}-----\n${rows.join("\n")}\n-----END ${upperCaseTag}-----`;
    }
    static isPEM(data) {
        return /-----BEGIN .+-----[A-Za-z0-9+/+=\s\n]+-----END .+-----/i.test(data);
    }
    static getTagName(pem) {
        if (!this.isPEM(pem)) {
            throw new Error("Bad parameter. Incoming data is not right PEM");
        }
        const res = /-----BEGIN (.+)-----/.exec(pem);
        if (!res) {
            throw new Error("Cannot get tag from PEM");
        }
        return res[1];
    }
    static hasTagName(pem, tagName) {
        const tag = this.getTagName(pem);
        return tagName.toLowerCase() === tag.toLowerCase();
    }
    static isCertificate(pem) {
        return this.hasTagName(pem, "certificate");
    }
    static isCertificateRequest(pem) {
        return this.hasTagName(pem, "certificate request");
    }
    static isCRL(pem) {
        return this.hasTagName(pem, "x509 crl");
    }
    static isPublicKey(pem) {
        return this.hasTagName(pem, "public key");
    }
}

function isJWK(data) {
    return typeof data === "object" && "kty" in data;
}

class ProviderCrypto {
    async digest(...args) {
        this.checkDigest.apply(this, args);
        return this.onDigest.apply(this, args);
    }
    checkDigest(algorithm, _data) {
        this.checkAlgorithmName(algorithm);
    }
    async onDigest(_algorithm, _data) {
        throw new UnsupportedOperationError("digest");
    }
    async generateKey(...args) {
        this.checkGenerateKey.apply(this, args);
        return this.onGenerateKey.apply(this, args);
    }
    checkGenerateKey(algorithm, _extractable, keyUsages, ..._args) {
        this.checkAlgorithmName(algorithm);
        this.checkGenerateKeyParams(algorithm);
        if (!(keyUsages && keyUsages.length)) {
            throw new TypeError("Usages cannot be empty when creating a key.");
        }
        let allowedUsages;
        if (Array.isArray(this.usages)) {
            allowedUsages = this.usages;
        }
        else {
            allowedUsages = this.usages.privateKey.concat(this.usages.publicKey);
        }
        this.checkKeyUsages(keyUsages, allowedUsages);
    }
    checkGenerateKeyParams(_algorithm) {
    }
    async onGenerateKey(_algorithm, _extractable, _keyUsages, ..._args) {
        throw new UnsupportedOperationError("generateKey");
    }
    async sign(...args) {
        this.checkSign.apply(this, args);
        return this.onSign.apply(this, args);
    }
    checkSign(algorithm, key, _data, ..._args) {
        this.checkAlgorithmName(algorithm);
        this.checkAlgorithmParams(algorithm);
        this.checkCryptoKey(key, "sign");
    }
    async onSign(_algorithm, _key, _data, ..._args) {
        throw new UnsupportedOperationError("sign");
    }
    async verify(...args) {
        this.checkVerify.apply(this, args);
        return this.onVerify.apply(this, args);
    }
    checkVerify(algorithm, key, _signature, _data, ..._args) {
        this.checkAlgorithmName(algorithm);
        this.checkAlgorithmParams(algorithm);
        this.checkCryptoKey(key, "verify");
    }
    async onVerify(_algorithm, _key, _signature, _data, ..._args) {
        throw new UnsupportedOperationError("verify");
    }
    async encrypt(...args) {
        this.checkEncrypt.apply(this, args);
        return this.onEncrypt.apply(this, args);
    }
    checkEncrypt(algorithm, key, _data, options = {}, ..._args) {
        this.checkAlgorithmName(algorithm);
        this.checkAlgorithmParams(algorithm);
        this.checkCryptoKey(key, options.keyUsage ? "encrypt" : void 0);
    }
    async onEncrypt(_algorithm, _key, _data, ..._args) {
        throw new UnsupportedOperationError("encrypt");
    }
    async decrypt(...args) {
        this.checkDecrypt.apply(this, args);
        return this.onDecrypt.apply(this, args);
    }
    checkDecrypt(algorithm, key, _data, options = {}, ..._args) {
        this.checkAlgorithmName(algorithm);
        this.checkAlgorithmParams(algorithm);
        this.checkCryptoKey(key, options.keyUsage ? "decrypt" : void 0);
    }
    async onDecrypt(_algorithm, _key, _data, ..._args) {
        throw new UnsupportedOperationError("decrypt");
    }
    async deriveBits(...args) {
        this.checkDeriveBits.apply(this, args);
        return this.onDeriveBits.apply(this, args);
    }
    checkDeriveBits(algorithm, baseKey, length, options = {}, ..._args) {
        this.checkAlgorithmName(algorithm);
        this.checkAlgorithmParams(algorithm);
        this.checkCryptoKey(baseKey, options.keyUsage ? "deriveBits" : void 0);
        if (length % 8 !== 0) {
            throw new OperationError("length: Is not multiple of 8");
        }
    }
    async onDeriveBits(_algorithm, _baseKey, _length, ..._args) {
        throw new UnsupportedOperationError("deriveBits");
    }
    async exportKey(...args) {
        this.checkExportKey.apply(this, args);
        return this.onExportKey.apply(this, args);
    }
    checkExportKey(format, key, ..._args) {
        this.checkKeyFormat(format);
        this.checkCryptoKey(key);
        if (!key.extractable) {
            throw new CryptoError("key: Is not extractable");
        }
    }
    async onExportKey(_format, _key, ..._args) {
        throw new UnsupportedOperationError("exportKey");
    }
    async importKey(...args) {
        this.checkImportKey.apply(this, args);
        return this.onImportKey.apply(this, args);
    }
    checkImportKey(format, keyData, algorithm, _extractable, keyUsages, ..._args) {
        this.checkKeyFormat(format);
        this.checkKeyData(format, keyData);
        this.checkAlgorithmName(algorithm);
        this.checkImportParams(algorithm);
        if (Array.isArray(this.usages)) {
            this.checkKeyUsages(keyUsages, this.usages);
        }
    }
    async onImportKey(_format, _keyData, _algorithm, _extractable, _keyUsages, ..._args) {
        throw new UnsupportedOperationError("importKey");
    }
    checkAlgorithmName(algorithm) {
        if (algorithm.name.toLowerCase() !== this.name.toLowerCase()) {
            throw new AlgorithmError("Unrecognized name");
        }
    }
    checkAlgorithmParams(_algorithm) {
    }
    checkDerivedKeyParams(_algorithm) {
    }
    checkKeyUsages(usages, allowed) {
        for (const usage of usages) {
            if (allowed.indexOf(usage) === -1) {
                throw new TypeError("Cannot create a key using the specified key usages");
            }
        }
    }
    checkCryptoKey(key, keyUsage) {
        this.checkAlgorithmName(key.algorithm);
        if (keyUsage && key.usages.indexOf(keyUsage) === -1) {
            throw new CryptoError("key does not match that of operation");
        }
    }
    checkRequiredProperty(data, propName) {
        if (!(propName in data)) {
            throw new RequiredPropertyError(propName);
        }
    }
    checkHashAlgorithm(algorithm, hashAlgorithms) {
        for (const item of hashAlgorithms) {
            if (item.toLowerCase() === algorithm.name.toLowerCase()) {
                return;
            }
        }
        throw new OperationError(`hash: Must be one of ${hashAlgorithms.join(", ")}`);
    }
    checkImportParams(_algorithm) {
    }
    checkKeyFormat(format) {
        switch (format) {
            case "raw":
            case "pkcs8":
            case "spki":
            case "jwk":
                break;
            default:
                throw new TypeError("format: Is invalid value. Must be 'jwk', 'raw', 'spki', or 'pkcs8'");
        }
    }
    checkKeyData(format, keyData) {
        if (!keyData) {
            throw new TypeError("keyData: Cannot be empty on empty on key importing");
        }
        if (format === "jwk") {
            if (!isJWK(keyData)) {
                throw new TypeError("keyData: Is not JsonWebToken");
            }
        }
        else if (!bytes.isBufferSource(keyData)) {
            throw new TypeError("keyData: Is not ArrayBufferView or ArrayBuffer");
        }
    }
    prepareData(data) {
        return bytes.toArrayBuffer(data);
    }
}

class AesProvider extends ProviderCrypto {
    checkGenerateKeyParams(algorithm) {
        this.checkRequiredProperty(algorithm, "length");
        if (typeof algorithm.length !== "number") {
            throw new TypeError("length: Is not of type Number");
        }
        switch (algorithm.length) {
            case 128:
            case 192:
            case 256:
                break;
            default:
                throw new TypeError("length: Must be 128, 192, or 256");
        }
    }
    checkDerivedKeyParams(algorithm) {
        this.checkGenerateKeyParams(algorithm);
    }
}

class AesCbcProvider extends AesProvider {
    name = "AES-CBC";
    usages = ["encrypt", "decrypt", "wrapKey", "unwrapKey"];
    checkAlgorithmParams(algorithm) {
        this.checkRequiredProperty(algorithm, "iv");
        if (!(algorithm.iv instanceof ArrayBuffer || ArrayBuffer.isView(algorithm.iv))) {
            throw new TypeError("iv: Is not of type '(ArrayBuffer or ArrayBufferView)'");
        }
        if (algorithm.iv.byteLength !== 16) {
            throw new TypeError("iv: Must have length 16 bytes");
        }
    }
}

class AesCmacProvider extends AesProvider {
    name = "AES-CMAC";
    usages = ["sign", "verify"];
    checkAlgorithmParams(algorithm) {
        this.checkRequiredProperty(algorithm, "length");
        if (typeof algorithm.length !== "number") {
            throw new TypeError("length: Is not a Number");
        }
        if (algorithm.length < 1) {
            throw new OperationError("length: Must be more than 0");
        }
    }
}

class AesCtrProvider extends AesProvider {
    name = "AES-CTR";
    usages = ["encrypt", "decrypt", "wrapKey", "unwrapKey"];
    checkAlgorithmParams(algorithm) {
        this.checkRequiredProperty(algorithm, "counter");
        if (!(algorithm.counter instanceof ArrayBuffer || ArrayBuffer.isView(algorithm.counter))) {
            throw new TypeError("counter: Is not of type '(ArrayBuffer or ArrayBufferView)'");
        }
        if (algorithm.counter.byteLength !== 16) {
            throw new TypeError("iv: Must have length 16 bytes");
        }
        this.checkRequiredProperty(algorithm, "length");
        if (typeof algorithm.length !== "number") {
            throw new TypeError("length: Is not a Number");
        }
        if (algorithm.length < 1) {
            throw new OperationError("length: Must be more than 0");
        }
    }
}

class AesEcbProvider extends AesProvider {
    name = "AES-ECB";
    usages = ["encrypt", "decrypt", "wrapKey", "unwrapKey"];
}

class AesGcmProvider extends AesProvider {
    name = "AES-GCM";
    usages = ["encrypt", "decrypt", "wrapKey", "unwrapKey"];
    checkAlgorithmParams(algorithm) {
        this.checkRequiredProperty(algorithm, "iv");
        if (!(algorithm.iv instanceof ArrayBuffer || ArrayBuffer.isView(algorithm.iv))) {
            throw new TypeError("iv: Is not of type '(ArrayBuffer or ArrayBufferView)'");
        }
        if (algorithm.iv.byteLength < 1) {
            throw new OperationError("iv: Must have length more than 0 and less than 2^64 - 1");
        }
        algorithm.tagLength ??= 128;
        switch (algorithm.tagLength) {
            case 32:
            case 64:
            case 96:
            case 104:
            case 112:
            case 120:
            case 128:
                break;
            default:
                throw new OperationError("tagLength: Must be one of 32, 64, 96, 104, 112, 120 or 128");
        }
    }
}

class AesKwProvider extends AesProvider {
    name = "AES-KW";
    usages = ["wrapKey", "unwrapKey"];
}

class DesProvider extends ProviderCrypto {
    usages = ["encrypt", "decrypt", "wrapKey", "unwrapKey"];
    checkAlgorithmParams(algorithm) {
        if (this.ivSize) {
            this.checkRequiredProperty(algorithm, "iv");
            if (!(algorithm.iv instanceof ArrayBuffer || ArrayBuffer.isView(algorithm.iv))) {
                throw new TypeError("iv: Is not of type '(ArrayBuffer or ArrayBufferView)'");
            }
            if (algorithm.iv.byteLength !== this.ivSize) {
                throw new TypeError(`iv: Must have length ${this.ivSize} bytes`);
            }
        }
    }
    checkGenerateKeyParams(algorithm) {
        this.checkRequiredProperty(algorithm, "length");
        if (typeof algorithm.length !== "number") {
            throw new TypeError("length: Is not of type Number");
        }
        if (algorithm.length !== this.keySizeBits) {
            throw new OperationError(`algorithm.length: Must be ${this.keySizeBits}`);
        }
    }
    checkDerivedKeyParams(algorithm) {
        this.checkGenerateKeyParams(algorithm);
    }
}

class RsaProvider extends ProviderCrypto {
    hashAlgorithms = ["SHA-1", "SHA-256", "SHA-384", "SHA-512"];
    checkGenerateKeyParams(algorithm) {
        this.checkRequiredProperty(algorithm, "hash");
        this.checkHashAlgorithm(algorithm.hash, this.hashAlgorithms);
        this.checkRequiredProperty(algorithm, "publicExponent");
        if (!(algorithm.publicExponent && algorithm.publicExponent instanceof Uint8Array)) {
            throw new TypeError("publicExponent: Missing or not a Uint8Array");
        }
        const publicExponent = encoding.base64url.encode(algorithm.publicExponent);
        if (!(publicExponent === "Aw==" || publicExponent === "AQAB")) {
            throw new TypeError("publicExponent: Must be [3] or [1,0,1]");
        }
        this.checkRequiredProperty(algorithm, "modulusLength");
        if (algorithm.modulusLength % 8
            || algorithm.modulusLength < 256
            || algorithm.modulusLength > 16384) {
            throw new TypeError("The modulus length must be a multiple of 8 bits and >= 256 and <= 16384");
        }
    }
    checkImportParams(algorithm) {
        this.checkRequiredProperty(algorithm, "hash");
        this.checkHashAlgorithm(algorithm.hash, this.hashAlgorithms);
    }
}

class RsaSsaProvider extends RsaProvider {
    name = "RSASSA-PKCS1-v1_5";
    usages = {
        privateKey: ["sign"],
        publicKey: ["verify"],
    };
}

class RsaPssProvider extends RsaProvider {
    name = "RSA-PSS";
    usages = {
        privateKey: ["sign"],
        publicKey: ["verify"],
    };
    checkAlgorithmParams(algorithm) {
        this.checkRequiredProperty(algorithm, "saltLength");
        if (typeof algorithm.saltLength !== "number") {
            throw new TypeError("saltLength: Is not a Number");
        }
        if (algorithm.saltLength < 0) {
            throw new RangeError("saltLength: Must be positive number");
        }
    }
}

class RsaOaepProvider extends RsaProvider {
    name = "RSA-OAEP";
    usages = {
        privateKey: ["decrypt", "unwrapKey"],
        publicKey: ["encrypt", "wrapKey"],
    };
    checkAlgorithmParams(algorithm) {
        if (algorithm.label
            && !(algorithm.label instanceof ArrayBuffer || ArrayBuffer.isView(algorithm.label))) {
            throw new TypeError("label: Is not of type '(ArrayBuffer or ArrayBufferView)'");
        }
    }
}

class EllipticProvider extends ProviderCrypto {
    checkGenerateKeyParams(algorithm) {
        this.checkRequiredProperty(algorithm, "namedCurve");
        this.checkNamedCurve(algorithm.namedCurve);
    }
    checkNamedCurve(namedCurve) {
        for (const item of this.namedCurves) {
            if (item.toLowerCase() === namedCurve.toLowerCase()) {
                return;
            }
        }
        throw new OperationError(`namedCurve: Must be one of ${this.namedCurves.join(", ")}`);
    }
}

class EcdsaProvider extends EllipticProvider {
    name = "ECDSA";
    hashAlgorithms = ["SHA-1", "SHA-256", "SHA-384", "SHA-512"];
    usages = {
        privateKey: ["sign"],
        publicKey: ["verify"],
    };
    namedCurves = ["P-256", "P-384", "P-521", "K-256"];
    checkAlgorithmParams(algorithm) {
        this.checkRequiredProperty(algorithm, "hash");
        this.checkHashAlgorithm(algorithm.hash, this.hashAlgorithms);
    }
}

const KEY_TYPES = ["secret", "private", "public"];
class CryptoKey {
    static create(algorithm, type, extractable, usages) {
        const key = new this();
        key.algorithm = algorithm;
        key.type = type;
        key.extractable = extractable;
        key.usages = usages;
        return key;
    }
    static isKeyType(data) {
        return KEY_TYPES.indexOf(data) !== -1;
    }
    algorithm;
    type;
    usages;
    extractable;
    [Symbol.toStringTag] = "CryptoKey";
}

class EcdhProvider extends EllipticProvider {
    name = "ECDH";
    usages = {
        privateKey: ["deriveBits", "deriveKey"],
        publicKey: [],
    };
    namedCurves = ["P-256", "P-384", "P-521", "K-256"];
    checkAlgorithmParams(algorithm) {
        this.checkRequiredProperty(algorithm, "public");
        if (!(algorithm.public instanceof CryptoKey)) {
            throw new TypeError("public: Is not a CryptoKey");
        }
        if (algorithm.public.type !== "public") {
            throw new OperationError("public: Is not a public key");
        }
        if (algorithm.public.algorithm.name !== this.name) {
            throw new OperationError(`public: Is not ${this.name} key`);
        }
    }
}

class EcdhEsProvider extends EcdhProvider {
    name = "ECDH-ES";
    namedCurves = ["X25519", "X448"];
}

class EdDsaProvider extends EllipticProvider {
    name = "EdDSA";
    usages = {
        privateKey: ["sign"],
        publicKey: ["verify"],
    };
    namedCurves = ["Ed25519", "Ed448"];
}

let ObjectIdentifier = class ObjectIdentifier {
    value;
    constructor(value) {
        if (value) {
            this.value = value;
        }
    }
};
__decorate([
    AsnProp({ type: AsnPropTypes.ObjectIdentifier })
], ObjectIdentifier.prototype, "value", void 0);
ObjectIdentifier = __decorate([
    AsnType({ type: AsnTypeTypes.Choice })
], ObjectIdentifier);

class AlgorithmIdentifier {
    algorithm;
    parameters;
    constructor(params) {
        Object.assign(this, params);
    }
}
__decorate([
    AsnProp({ type: AsnPropTypes.ObjectIdentifier })
], AlgorithmIdentifier.prototype, "algorithm", void 0);
__decorate([
    AsnProp({
        type: AsnPropTypes.Any,
        optional: true,
    })
], AlgorithmIdentifier.prototype, "parameters", void 0);

class PrivateKeyInfo {
    version = 0;
    privateKeyAlgorithm = new AlgorithmIdentifier();
    privateKey = new ArrayBuffer(0);
    attributes;
}
__decorate([
    AsnProp({ type: AsnPropTypes.Integer })
], PrivateKeyInfo.prototype, "version", void 0);
__decorate([
    AsnProp({ type: AlgorithmIdentifier })
], PrivateKeyInfo.prototype, "privateKeyAlgorithm", void 0);
__decorate([
    AsnProp({ type: AsnPropTypes.OctetString })
], PrivateKeyInfo.prototype, "privateKey", void 0);
__decorate([
    AsnProp({
        type: AsnPropTypes.Any, optional: true,
    })
], PrivateKeyInfo.prototype, "attributes", void 0);

class PublicKeyInfo {
    publicKeyAlgorithm = new AlgorithmIdentifier();
    publicKey = new ArrayBuffer(0);
}
__decorate([
    AsnProp({ type: AlgorithmIdentifier })
], PublicKeyInfo.prototype, "publicKeyAlgorithm", void 0);
__decorate([
    AsnProp({ type: AsnPropTypes.BitString })
], PublicKeyInfo.prototype, "publicKey", void 0);

const JsonBase64UrlArrayBufferConverter = {
    fromJSON: (value) => bytes.toArrayBuffer(encoding.base64url.decode(value)),
    toJSON: (value) => encoding.base64url.encode(value),
};

const AsnIntegerArrayBufferConverter = {
    fromASN: (value) => {
        const valueHex = value.valueBlock.valueHex;
        return !(new Uint8Array(valueHex)[0])
            ? value.valueBlock.valueHex.slice(1)
            : value.valueBlock.valueHex;
    },
    toASN: (value) => {
        const valueHex = new Uint8Array(value)[0] > 127
            ? bytes.concat(new Uint8Array([0]).buffer, value)
            : value;
        return new asn1.Integer({ valueHex });
    },
};

var index$3 = /*#__PURE__*/Object.freeze({
    __proto__: null,
    AsnIntegerArrayBufferConverter: AsnIntegerArrayBufferConverter,
    JsonBase64UrlArrayBufferConverter: JsonBase64UrlArrayBufferConverter
});

class RsaPrivateKey {
    version = 0;
    modulus = new ArrayBuffer(0);
    publicExponent = new ArrayBuffer(0);
    privateExponent = new ArrayBuffer(0);
    prime1 = new ArrayBuffer(0);
    prime2 = new ArrayBuffer(0);
    exponent1 = new ArrayBuffer(0);
    exponent2 = new ArrayBuffer(0);
    coefficient = new ArrayBuffer(0);
    otherPrimeInfos;
}
__decorate([
    AsnProp({
        type: AsnPropTypes.Integer, converter: AsnIntegerConverter,
    })
], RsaPrivateKey.prototype, "version", void 0);
__decorate([
    AsnProp({
        type: AsnPropTypes.Integer, converter: AsnIntegerArrayBufferConverter,
    }),
    JsonProp({
        name: "n", converter: JsonBase64UrlArrayBufferConverter,
    })
], RsaPrivateKey.prototype, "modulus", void 0);
__decorate([
    AsnProp({
        type: AsnPropTypes.Integer, converter: AsnIntegerArrayBufferConverter,
    }),
    JsonProp({
        name: "e", converter: JsonBase64UrlArrayBufferConverter,
    })
], RsaPrivateKey.prototype, "publicExponent", void 0);
__decorate([
    AsnProp({
        type: AsnPropTypes.Integer, converter: AsnIntegerArrayBufferConverter,
    }),
    JsonProp({
        name: "d", converter: JsonBase64UrlArrayBufferConverter,
    })
], RsaPrivateKey.prototype, "privateExponent", void 0);
__decorate([
    AsnProp({
        type: AsnPropTypes.Integer, converter: AsnIntegerArrayBufferConverter,
    }),
    JsonProp({
        name: "p", converter: JsonBase64UrlArrayBufferConverter,
    })
], RsaPrivateKey.prototype, "prime1", void 0);
__decorate([
    AsnProp({
        type: AsnPropTypes.Integer, converter: AsnIntegerArrayBufferConverter,
    }),
    JsonProp({
        name: "q", converter: JsonBase64UrlArrayBufferConverter,
    })
], RsaPrivateKey.prototype, "prime2", void 0);
__decorate([
    AsnProp({
        type: AsnPropTypes.Integer, converter: AsnIntegerArrayBufferConverter,
    }),
    JsonProp({
        name: "dp", converter: JsonBase64UrlArrayBufferConverter,
    })
], RsaPrivateKey.prototype, "exponent1", void 0);
__decorate([
    AsnProp({
        type: AsnPropTypes.Integer, converter: AsnIntegerArrayBufferConverter,
    }),
    JsonProp({
        name: "dq", converter: JsonBase64UrlArrayBufferConverter,
    })
], RsaPrivateKey.prototype, "exponent2", void 0);
__decorate([
    AsnProp({
        type: AsnPropTypes.Integer, converter: AsnIntegerArrayBufferConverter,
    }),
    JsonProp({
        name: "qi", converter: JsonBase64UrlArrayBufferConverter,
    })
], RsaPrivateKey.prototype, "coefficient", void 0);
__decorate([
    AsnProp({
        type: AsnPropTypes.Any, optional: true,
    })
], RsaPrivateKey.prototype, "otherPrimeInfos", void 0);

class RsaPublicKey {
    modulus = new ArrayBuffer(0);
    publicExponent = new ArrayBuffer(0);
}
__decorate([
    AsnProp({
        type: AsnPropTypes.Integer, converter: AsnIntegerArrayBufferConverter,
    }),
    JsonProp({
        name: "n", converter: JsonBase64UrlArrayBufferConverter,
    })
], RsaPublicKey.prototype, "modulus", void 0);
__decorate([
    AsnProp({
        type: AsnPropTypes.Integer, converter: AsnIntegerArrayBufferConverter,
    }),
    JsonProp({
        name: "e", converter: JsonBase64UrlArrayBufferConverter,
    })
], RsaPublicKey.prototype, "publicExponent", void 0);

let EcPublicKey = class EcPublicKey {
    value = new ArrayBuffer(0);
    constructor(value) {
        if (value) {
            this.value = value;
        }
    }
    toJSON() {
        let bytes = new Uint8Array(this.value);
        if (bytes[0] !== 0x04) {
            throw new CryptoError("Wrong ECPoint. Current version supports only Uncompressed (0x04) point");
        }
        bytes = new Uint8Array(this.value.slice(1));
        const size = bytes.length / 2;
        const offset = 0;
        const json = {
            x: encoding.base64url.encode(bytes.buffer.slice(offset, offset + size)),
            y: encoding.base64url.encode(bytes.buffer.slice(offset + size, offset + size + size)),
        };
        return json;
    }
    fromJSON(json) {
        if (!("x" in json)) {
            throw new Error("x: Missing required property");
        }
        if (!("y" in json)) {
            throw new Error("y: Missing required property");
        }
        const x = encoding.base64url.decode(json.x);
        const y = encoding.base64url.decode(json.y);
        const value = bytes.concat(new Uint8Array([0x04]).buffer, x, y);
        this.value = bytes.toArrayBuffer(value);
        return this;
    }
};
__decorate([
    AsnProp({ type: AsnPropTypes.OctetString })
], EcPublicKey.prototype, "value", void 0);
EcPublicKey = __decorate([
    AsnType({ type: AsnTypeTypes.Choice })
], EcPublicKey);

class EcPrivateKey {
    version = 1;
    privateKey = new ArrayBuffer(0);
    parameters;
    publicKey;
    fromJSON(json) {
        if (!("d" in json)) {
            throw new Error("d: Missing required property");
        }
        this.privateKey = bytes.toArrayBuffer(encoding.base64url.decode(json.d));
        if ("x" in json) {
            const publicKey = new EcPublicKey();
            publicKey.fromJSON(json);
            const asn = AsnSerializer.toASN(publicKey);
            if ("valueHex" in asn.valueBlock) {
                this.publicKey = asn.valueBlock.valueHex;
            }
        }
        return this;
    }
    toJSON() {
        const jwk = {};
        jwk.d = encoding.base64url.encode(this.privateKey);
        if (this.publicKey) {
            Object.assign(jwk, new EcPublicKey(this.publicKey).toJSON());
        }
        return jwk;
    }
}
__decorate([
    AsnProp({
        type: AsnPropTypes.Integer, converter: AsnIntegerConverter,
    })
], EcPrivateKey.prototype, "version", void 0);
__decorate([
    AsnProp({ type: AsnPropTypes.OctetString })
], EcPrivateKey.prototype, "privateKey", void 0);
__decorate([
    AsnProp({
        context: 0, type: AsnPropTypes.Any, optional: true,
    })
], EcPrivateKey.prototype, "parameters", void 0);
__decorate([
    AsnProp({
        context: 1, type: AsnPropTypes.BitString, optional: true,
    })
], EcPrivateKey.prototype, "publicKey", void 0);

class EcUtils {
    static decodePoint(data, pointSize) {
        const view = bytes.toUint8Array(data);
        if ((view.length === 0) || (view[0] !== 4)) {
            throw new Error("Only uncompressed point format supported");
        }
        const n = (view.length - 1) / 2;
        if (n !== (Math.ceil(pointSize / 8))) {
            throw new Error("Point does not match field size");
        }
        const xb = view.slice(1, n + 1);
        const yb = view.slice(n + 1, n + 1 + n);
        return {
            x: xb, y: yb,
        };
    }
    static encodePoint(point, pointSize) {
        const size = Math.ceil(pointSize / 8);
        if (point.x.byteLength !== size || point.y.byteLength !== size) {
            throw new Error("X,Y coordinates don't match point size criteria");
        }
        const x = bytes.toUint8Array(point.x);
        const y = bytes.toUint8Array(point.y);
        const res = new Uint8Array(size * 2 + 1);
        res[0] = 4;
        res.set(x, 1);
        res.set(y, size + 1);
        return res;
    }
    static getSize(pointSize) {
        return Math.ceil(pointSize / 8);
    }
    static encodeSignature(signature, pointSize) {
        const size = this.getSize(pointSize);
        const r = bytes.toUint8Array(signature.r);
        const s = bytes.toUint8Array(signature.s);
        const res = new Uint8Array(size * 2);
        res.set(this.padStart(r, size));
        res.set(this.padStart(s, size), size);
        return res;
    }
    static decodeSignature(data, pointSize) {
        const size = this.getSize(pointSize);
        const view = bytes.toUint8Array(data);
        if (view.length !== (size * 2)) {
            throw new Error("Incorrect size of the signature");
        }
        const r = view.slice(0, size);
        const s = view.slice(size);
        return {
            r: bytes.toArrayBuffer(this.trimStart(r)),
            s: bytes.toArrayBuffer(this.trimStart(s)),
        };
    }
    static trimStart(data) {
        let i = 0;
        while ((i < data.length - 1) && (data[i] === 0)) {
            i++;
        }
        if (i === 0) {
            return data;
        }
        return data.slice(i, data.length);
    }
    static padStart(data, size) {
        if (size === data.length) {
            return data;
        }
        const res = new Uint8Array(size);
        res.set(data, size - data.length);
        return res;
    }
}

const AsnIntegerWithoutPaddingConverter = {
    fromASN: (value) => {
        const bytes = new Uint8Array(value.valueBlock.valueHex);
        return (bytes[0] === 0)
            ? bytes.buffer.slice(1)
            : bytes.buffer;
    },
    toASN: (value) => {
        const bytes = new Uint8Array(value);
        if (bytes[0] > 127) {
            const newValue = new Uint8Array(bytes.length + 1);
            newValue.set(bytes, 1);
            return new asn1.Integer({ valueHex: newValue.buffer });
        }
        return new asn1.Integer({ valueHex: value });
    },
};

var index$2 = /*#__PURE__*/Object.freeze({
    __proto__: null,
    AsnIntegerWithoutPaddingConverter: AsnIntegerWithoutPaddingConverter
});

class EcDsaSignature {
    static fromWebCryptoSignature(value) {
        const pointSize = value.byteLength / 2;
        const point = EcUtils.decodeSignature(value, pointSize * 8);
        const ecSignature = new EcDsaSignature();
        ecSignature.r = bytes.toArrayBuffer(point.r);
        ecSignature.s = bytes.toArrayBuffer(point.s);
        return ecSignature;
    }
    r = new ArrayBuffer(0);
    s = new ArrayBuffer(0);
    toWebCryptoSignature(pointSize) {
        if (!pointSize) {
            const maxPointLength = Math.max(this.r.byteLength, this.s.byteLength);
            if (maxPointLength <= 32) {
                pointSize = 256;
            }
            else if (maxPointLength <= 48) {
                pointSize = 384;
            }
            else {
                pointSize = 521;
            }
        }
        const signature = EcUtils.encodeSignature(this, pointSize);
        return bytes.toArrayBuffer(signature);
    }
}
__decorate([
    AsnProp({
        type: AsnPropTypes.Integer, converter: AsnIntegerWithoutPaddingConverter,
    })
], EcDsaSignature.prototype, "r", void 0);
__decorate([
    AsnProp({
        type: AsnPropTypes.Integer, converter: AsnIntegerWithoutPaddingConverter,
    })
], EcDsaSignature.prototype, "s", void 0);

class OneAsymmetricKey extends PrivateKeyInfo {
    publicKey;
}
__decorate([
    AsnProp({
        context: 1, implicit: true, type: AsnPropTypes.BitString, optional: true,
    })
], OneAsymmetricKey.prototype, "publicKey", void 0);

let EdPrivateKey = class EdPrivateKey {
    value = new ArrayBuffer(0);
    fromJSON(json) {
        if (!json.d) {
            throw new Error("d: Missing required property");
        }
        this.value = bytes.toArrayBuffer(encoding.base64url.decode(json.d));
        return this;
    }
    toJSON() {
        const jwk = { d: encoding.base64url.encode(this.value) };
        return jwk;
    }
};
__decorate([
    AsnProp({ type: AsnPropTypes.OctetString })
], EdPrivateKey.prototype, "value", void 0);
EdPrivateKey = __decorate([
    AsnType({ type: AsnTypeTypes.Choice })
], EdPrivateKey);

let EdPublicKey = class EdPublicKey {
    value = new ArrayBuffer(0);
    constructor(value) {
        if (value) {
            this.value = value;
        }
    }
    toJSON() {
        const json = { x: encoding.base64url.encode(this.value) };
        return json;
    }
    fromJSON(json) {
        if (!("x" in json)) {
            throw new Error("x: Missing required property");
        }
        this.value = bytes.toArrayBuffer(encoding.base64url.decode(json.x));
        return this;
    }
};
__decorate([
    AsnProp({ type: AsnPropTypes.BitString })
], EdPublicKey.prototype, "value", void 0);
EdPublicKey = __decorate([
    AsnType({ type: AsnTypeTypes.Choice })
], EdPublicKey);

let CurvePrivateKey = class CurvePrivateKey {
    d;
};
__decorate([
    AsnProp({ type: AsnPropTypes.OctetString }),
    JsonProp({
        type: JsonPropTypes.String, converter: JsonBase64UrlArrayBufferConverter,
    })
], CurvePrivateKey.prototype, "d", void 0);
CurvePrivateKey = __decorate([
    AsnType({ type: AsnTypeTypes.Choice })
], CurvePrivateKey);

const idSecp256r1 = "1.2.840.10045.3.1.7";
const idEllipticCurve = "1.3.132.0";
const idSecp384r1 = `${idEllipticCurve}.34`;
const idSecp521r1 = `${idEllipticCurve}.35`;
const idSecp256k1 = `${idEllipticCurve}.10`;
const idVersionOne = "1.3.36.3.3.2.8.1.1";
const idBrainpoolP160r1 = `${idVersionOne}.1`;
const idBrainpoolP160t1 = `${idVersionOne}.2`;
const idBrainpoolP192r1 = `${idVersionOne}.3`;
const idBrainpoolP192t1 = `${idVersionOne}.4`;
const idBrainpoolP224r1 = `${idVersionOne}.5`;
const idBrainpoolP224t1 = `${idVersionOne}.6`;
const idBrainpoolP256r1 = `${idVersionOne}.7`;
const idBrainpoolP256t1 = `${idVersionOne}.8`;
const idBrainpoolP320r1 = `${idVersionOne}.9`;
const idBrainpoolP320t1 = `${idVersionOne}.10`;
const idBrainpoolP384r1 = `${idVersionOne}.11`;
const idBrainpoolP384t1 = `${idVersionOne}.12`;
const idBrainpoolP512r1 = `${idVersionOne}.13`;
const idBrainpoolP512t1 = `${idVersionOne}.14`;
const idX25519 = "1.3.101.110";
const idX448 = "1.3.101.111";
const idEd25519 = "1.3.101.112";
const idEd448 = "1.3.101.113";

var index$1 = /*#__PURE__*/Object.freeze({
    __proto__: null,
    AlgorithmIdentifier: AlgorithmIdentifier,
    get CurvePrivateKey () { return CurvePrivateKey; },
    EcDsaSignature: EcDsaSignature,
    EcPrivateKey: EcPrivateKey,
    get EcPublicKey () { return EcPublicKey; },
    get EdPrivateKey () { return EdPrivateKey; },
    get EdPublicKey () { return EdPublicKey; },
    get ObjectIdentifier () { return ObjectIdentifier; },
    OneAsymmetricKey: OneAsymmetricKey,
    PrivateKeyInfo: PrivateKeyInfo,
    PublicKeyInfo: PublicKeyInfo,
    RsaPrivateKey: RsaPrivateKey,
    RsaPublicKey: RsaPublicKey,
    converters: index$2,
    idBrainpoolP160r1: idBrainpoolP160r1,
    idBrainpoolP160t1: idBrainpoolP160t1,
    idBrainpoolP192r1: idBrainpoolP192r1,
    idBrainpoolP192t1: idBrainpoolP192t1,
    idBrainpoolP224r1: idBrainpoolP224r1,
    idBrainpoolP224t1: idBrainpoolP224t1,
    idBrainpoolP256r1: idBrainpoolP256r1,
    idBrainpoolP256t1: idBrainpoolP256t1,
    idBrainpoolP320r1: idBrainpoolP320r1,
    idBrainpoolP320t1: idBrainpoolP320t1,
    idBrainpoolP384r1: idBrainpoolP384r1,
    idBrainpoolP384t1: idBrainpoolP384t1,
    idBrainpoolP512r1: idBrainpoolP512r1,
    idBrainpoolP512t1: idBrainpoolP512t1,
    idEd25519: idEd25519,
    idEd448: idEd448,
    idEllipticCurve: idEllipticCurve,
    idSecp256k1: idSecp256k1,
    idSecp256r1: idSecp256r1,
    idSecp384r1: idSecp384r1,
    idSecp521r1: idSecp521r1,
    idVersionOne: idVersionOne,
    idX25519: idX25519,
    idX448: idX448
});

class EcCurves {
    static items = [];
    static names = [];
    static register(item) {
        const oid = new ObjectIdentifier();
        oid.value = item.id;
        const raw = AsnConvert.serialize(oid);
        this.items.push({
            ...item,
            raw,
        });
        this.names.push(item.name);
    }
    static find(nameOrId) {
        nameOrId = nameOrId.toUpperCase();
        for (const item of this.items) {
            if (item.name.toUpperCase() === nameOrId || item.id.toUpperCase() === nameOrId) {
                return item;
            }
        }
        return null;
    }
    static get(nameOrId) {
        const res = this.find(nameOrId);
        if (!res) {
            throw new Error(`Unsupported EC named curve '${nameOrId}'`);
        }
        return res;
    }
}
EcCurves.register({
    name: "P-256", id: idSecp256r1, size: 256,
});
EcCurves.register({
    name: "P-384", id: idSecp384r1, size: 384,
});
EcCurves.register({
    name: "P-521", id: idSecp521r1, size: 521,
});
EcCurves.register({
    name: "K-256", id: idSecp256k1, size: 256,
});
EcCurves.register({
    name: "brainpoolP160r1", id: idBrainpoolP160r1, size: 160,
});
EcCurves.register({
    name: "brainpoolP160t1", id: idBrainpoolP160t1, size: 160,
});
EcCurves.register({
    name: "brainpoolP192r1", id: idBrainpoolP192r1, size: 192,
});
EcCurves.register({
    name: "brainpoolP192t1", id: idBrainpoolP192t1, size: 192,
});
EcCurves.register({
    name: "brainpoolP224r1", id: idBrainpoolP224r1, size: 224,
});
EcCurves.register({
    name: "brainpoolP224t1", id: idBrainpoolP224t1, size: 224,
});
EcCurves.register({
    name: "brainpoolP256r1", id: idBrainpoolP256r1, size: 256,
});
EcCurves.register({
    name: "brainpoolP256t1", id: idBrainpoolP256t1, size: 256,
});
EcCurves.register({
    name: "brainpoolP320r1", id: idBrainpoolP320r1, size: 320,
});
EcCurves.register({
    name: "brainpoolP320t1", id: idBrainpoolP320t1, size: 320,
});
EcCurves.register({
    name: "brainpoolP384r1", id: idBrainpoolP384r1, size: 384,
});
EcCurves.register({
    name: "brainpoolP384t1", id: idBrainpoolP384t1, size: 384,
});
EcCurves.register({
    name: "brainpoolP512r1", id: idBrainpoolP512r1, size: 512,
});
EcCurves.register({
    name: "brainpoolP512t1", id: idBrainpoolP512t1, size: 512,
});

class X25519Provider extends ProviderCrypto {
    name = "X25519";
    usages = {
        privateKey: ["deriveKey", "deriveBits"],
        publicKey: [],
    };
    checkAlgorithmParams(algorithm) {
        this.checkRequiredProperty(algorithm, "public");
    }
}

class Ed25519Provider extends ProviderCrypto {
    name = "Ed25519";
    usages = {
        privateKey: ["sign"],
        publicKey: ["verify"],
    };
}

class HmacProvider extends ProviderCrypto {
    name = "HMAC";
    hashAlgorithms = ["SHA-1", "SHA-256", "SHA-384", "SHA-512"];
    usages = ["sign", "verify"];
    getDefaultLength(algName) {
        switch (algName.toUpperCase()) {
            case "SHA-1":
            case "SHA-256":
            case "SHA-384":
            case "SHA-512":
                return 512;
            default:
                throw new Error(`Unknown algorithm name '${algName}'`);
        }
    }
    checkGenerateKeyParams(algorithm) {
        this.checkRequiredProperty(algorithm, "hash");
        this.checkHashAlgorithm(algorithm.hash, this.hashAlgorithms);
        if ("length" in algorithm) {
            if (typeof algorithm.length !== "number") {
                throw new TypeError("length: Is not a Number");
            }
            if (algorithm.length < 1) {
                throw new RangeError("length: Number is out of range");
            }
        }
    }
    checkImportParams(algorithm) {
        this.checkRequiredProperty(algorithm, "hash");
        this.checkHashAlgorithm(algorithm.hash, this.hashAlgorithms);
    }
}

class Pbkdf2Provider extends ProviderCrypto {
    name = "PBKDF2";
    hashAlgorithms = ["SHA-1", "SHA-256", "SHA-384", "SHA-512"];
    usages = ["deriveBits", "deriveKey"];
    checkAlgorithmParams(algorithm) {
        this.checkRequiredProperty(algorithm, "hash");
        this.checkHashAlgorithm(algorithm.hash, this.hashAlgorithms);
        this.checkRequiredProperty(algorithm, "salt");
        if (!(algorithm.salt instanceof ArrayBuffer || ArrayBuffer.isView(algorithm.salt))) {
            throw new TypeError("salt: Is not of type '(ArrayBuffer or ArrayBufferView)'");
        }
        this.checkRequiredProperty(algorithm, "iterations");
        if (typeof algorithm.iterations !== "number") {
            throw new TypeError("iterations: Is not a Number");
        }
        if (algorithm.iterations < 1) {
            throw new TypeError("iterations: Is less than 1");
        }
    }
    checkImportKey(format, keyData, algorithm, extractable, keyUsages, ...args) {
        super.checkImportKey(format, keyData, algorithm, extractable, keyUsages, ...args);
        if (extractable) {
            throw new SyntaxError("extractable: Must be 'false'");
        }
    }
}

class HkdfProvider extends ProviderCrypto {
    name = "HKDF";
    hashAlgorithms = ["SHA-1", "SHA-256", "SHA-384", "SHA-512"];
    usages = ["deriveKey", "deriveBits"];
    checkAlgorithmParams(algorithm) {
        this.checkRequiredProperty(algorithm, "hash");
        this.checkHashAlgorithm(algorithm.hash, this.hashAlgorithms);
        this.checkRequiredProperty(algorithm, "salt");
        if (!bytes.isBufferSource(algorithm.salt)) {
            throw new TypeError("salt: Is not of type '(ArrayBuffer or ArrayBufferView)'");
        }
        this.checkRequiredProperty(algorithm, "info");
        if (!bytes.isBufferSource(algorithm.info)) {
            throw new TypeError("info: Is not of type '(ArrayBuffer or ArrayBufferView)'");
        }
    }
    checkImportKey(format, keyData, algorithm, extractable, keyUsages, ...args) {
        super.checkImportKey(format, keyData, algorithm, extractable, keyUsages, ...args);
        if (extractable) {
            throw new SyntaxError("extractable: Must be 'false'");
        }
    }
}

class ShakeProvider extends ProviderCrypto {
    usages = [];
    defaultLength = 0;
    digest(...args) {
        args[0] = {
            length: this.defaultLength, ...args[0],
        };
        return super.digest.apply(this, args);
    }
    checkDigest(algorithm, data) {
        super.checkDigest(algorithm, data);
        const length = algorithm.length || 0;
        if (typeof length !== "number") {
            throw new TypeError("length: Is not a Number");
        }
        if (length < 0) {
            throw new TypeError("length: Is negative");
        }
    }
}

class Shake128Provider extends ShakeProvider {
    name = "shake128";
    defaultLength = 16;
}

class Shake256Provider extends ShakeProvider {
    name = "shake256";
    defaultLength = 32;
}

class Crypto {
    [Symbol.toStringTag] = "Crypto";
    randomUUID() {
        const b = this.getRandomValues(new Uint8Array(16));
        b[6] = (b[6] & 0x0f) | 0x40;
        b[8] = (b[8] & 0x3f) | 0x80;
        const uuid = encoding.hex.encode(b, { case: "lower" });
        return `${uuid.substring(0, 8)}-${uuid.substring(8, 12)}-${uuid.substring(12, 16)}-${uuid.substring(16, 20)}-${uuid.substring(20)}`;
    }
}

class ProviderStorage {
    items = {};
    get(algorithmName) {
        return this.items[algorithmName.toLowerCase()] || null;
    }
    set(provider) {
        this.items[provider.name.toLowerCase()] = provider;
    }
    removeAt(algorithmName) {
        const provider = this.get(algorithmName.toLowerCase());
        if (provider) {
            delete this.items[algorithmName];
        }
        return provider;
    }
    has(name) {
        return !!this.get(name);
    }
    get length() {
        return Object.keys(this.items).length;
    }
    get algorithms() {
        const algorithms = [];
        for (const key in this.items) {
            const provider = this.items[key];
            algorithms.push(provider.name);
        }
        return algorithms.sort();
    }
}

const keyFormatMap = {
    jwk: ["private", "public", "secret"],
    pkcs8: ["private"],
    spki: ["public"],
    raw: ["secret", "public"],
};
const sourceBufferKeyFormats = ["pkcs8", "spki", "raw"];
class SubtleCrypto {
    static isHashedAlgorithm(data) {
        return data
            && typeof data === "object"
            && "name" in data
            && "hash" in data
            ? true
            : false;
    }
    providers = new ProviderStorage();
    [Symbol.toStringTag] = "SubtleCrypto";
    async digest(...args) {
        this.checkRequiredArguments(args, 2, "digest");
        const [algorithm, data, ...params] = args;
        const preparedAlgorithm = this.prepareAlgorithm(algorithm);
        const preparedData = bytes.toArrayBuffer(data);
        const provider = this.getProvider(preparedAlgorithm.name);
        const result = await provider.digest(preparedAlgorithm, preparedData, ...params);
        return result;
    }
    async generateKey(...args) {
        this.checkRequiredArguments(args, 3, "generateKey");
        const [algorithm, extractable, keyUsages, ...params] = args;
        const preparedAlgorithm = this.prepareAlgorithm(algorithm);
        const provider = this.getProvider(preparedAlgorithm.name);
        const result = await provider.generateKey({
            ...preparedAlgorithm, name: provider.name,
        }, extractable, keyUsages, ...params);
        return result;
    }
    async sign(...args) {
        this.checkRequiredArguments(args, 3, "sign");
        const [algorithm, key, data, ...params] = args;
        this.checkCryptoKey(key);
        const preparedAlgorithm = this.prepareAlgorithm(algorithm);
        const preparedData = bytes.toArrayBuffer(data);
        const provider = this.getProvider(preparedAlgorithm.name);
        const result = await provider.sign({
            ...preparedAlgorithm, name: provider.name,
        }, key, preparedData, ...params);
        return result;
    }
    async verify(...args) {
        this.checkRequiredArguments(args, 4, "verify");
        const [algorithm, key, signature, data, ...params] = args;
        this.checkCryptoKey(key);
        const preparedAlgorithm = this.prepareAlgorithm(algorithm);
        const preparedData = bytes.toArrayBuffer(data);
        const preparedSignature = bytes.toArrayBuffer(signature);
        const provider = this.getProvider(preparedAlgorithm.name);
        const result = await provider.verify({
            ...preparedAlgorithm, name: provider.name,
        }, key, preparedSignature, preparedData, ...params);
        return result;
    }
    async encrypt(...args) {
        this.checkRequiredArguments(args, 3, "encrypt");
        const [algorithm, key, data, ...params] = args;
        this.checkCryptoKey(key);
        const preparedAlgorithm = this.prepareAlgorithm(algorithm);
        const preparedData = bytes.toArrayBuffer(data);
        const provider = this.getProvider(preparedAlgorithm.name);
        const result = await provider.encrypt({
            ...preparedAlgorithm, name: provider.name,
        }, key, preparedData, { keyUsage: true }, ...params);
        return result;
    }
    async decrypt(...args) {
        this.checkRequiredArguments(args, 3, "decrypt");
        const [algorithm, key, data, ...params] = args;
        this.checkCryptoKey(key);
        const preparedAlgorithm = this.prepareAlgorithm(algorithm);
        const preparedData = bytes.toArrayBuffer(data);
        const provider = this.getProvider(preparedAlgorithm.name);
        const result = await provider.decrypt({
            ...preparedAlgorithm, name: provider.name,
        }, key, preparedData, { keyUsage: true }, ...params);
        return result;
    }
    async deriveBits(...args) {
        this.checkRequiredArguments(args, 3, "deriveBits");
        const [algorithm, baseKey, length, ...params] = args;
        this.checkCryptoKey(baseKey);
        const preparedAlgorithm = this.prepareAlgorithm(algorithm);
        const provider = this.getProvider(preparedAlgorithm.name);
        const result = await provider.deriveBits({
            ...preparedAlgorithm, name: provider.name,
        }, baseKey, length, { keyUsage: true }, ...params);
        return result;
    }
    async deriveKey(...args) {
        this.checkRequiredArguments(args, 5, "deriveKey");
        const [algorithm, baseKey, derivedKeyType, extractable, keyUsages, ...params] = args;
        const preparedDerivedKeyType = this.prepareAlgorithm(derivedKeyType);
        const importProvider = this.getProvider(preparedDerivedKeyType.name);
        importProvider.checkDerivedKeyParams(preparedDerivedKeyType);
        const preparedAlgorithm = this.prepareAlgorithm(algorithm);
        const provider = this.getProvider(preparedAlgorithm.name);
        provider.checkCryptoKey(baseKey, "deriveKey");
        const derivedBits = await provider.deriveBits({
            ...preparedAlgorithm, name: provider.name,
        }, baseKey, derivedKeyType.length || 512, { keyUsage: false }, ...params);
        return this.importKey("raw", derivedBits, derivedKeyType, extractable, keyUsages, ...params);
    }
    async exportKey(...args) {
        this.checkRequiredArguments(args, 2, "exportKey");
        const [format, key, ...params] = args;
        this.checkCryptoKey(key);
        if (!keyFormatMap[format]) {
            throw new TypeError("Invalid keyFormat argument");
        }
        if (!keyFormatMap[format].includes(key.type)) {
            throw new DOMException("The key is not of the expected type");
        }
        const provider = this.getProvider(key.algorithm.name);
        const result = await provider.exportKey(format, key, ...params);
        return result;
    }
    async importKey(...args) {
        this.checkRequiredArguments(args, 5, "importKey");
        const [format, keyData, algorithm, extractable, keyUsages, ...params] = args;
        const preparedAlgorithm = this.prepareAlgorithm(algorithm);
        const provider = this.getProvider(preparedAlgorithm.name);
        if (format === "jwk") {
            if (typeof keyData !== "object" || !keyData.kty) {
                throw new TypeError("Key data must be an object for JWK import");
            }
        }
        else if (sourceBufferKeyFormats.includes(format)) {
            if (!bytes.isBufferSource(keyData)) {
                throw new TypeError("Key data must be a BufferSource for non-JWK formats");
            }
        }
        else {
            throw new TypeError("The provided value is not of type '(ArrayBuffer or ArrayBufferView or JsonWebKey)'");
        }
        return provider.importKey(format, keyData, {
            ...preparedAlgorithm, name: provider.name,
        }, extractable, keyUsages, ...params);
    }
    async wrapKey(format, key, wrappingKey, wrapAlgorithm, ...args) {
        let keyData = await this.exportKey(format, key, ...args);
        if (format === "jwk") {
            const json = JSON.stringify(keyData);
            keyData = bytes.toArrayBuffer(encoding.utf8.encode(json));
        }
        const preparedAlgorithm = this.prepareAlgorithm(wrapAlgorithm);
        const preparedData = bytes.toArrayBuffer(keyData);
        const provider = this.getProvider(preparedAlgorithm.name);
        return provider.encrypt({
            ...preparedAlgorithm, name: provider.name,
        }, wrappingKey, preparedData, { keyUsage: false }, ...args);
    }
    async unwrapKey(format, wrappedKey, unwrappingKey, unwrapAlgorithm, unwrappedKeyAlgorithm, extractable, keyUsages, ...args) {
        const preparedAlgorithm = this.prepareAlgorithm(unwrapAlgorithm);
        const preparedData = bytes.toArrayBuffer(wrappedKey);
        const provider = this.getProvider(preparedAlgorithm.name);
        let keyData = await provider.decrypt({
            ...preparedAlgorithm, name: provider.name,
        }, unwrappingKey, preparedData, { keyUsage: false }, ...args);
        if (format === "jwk") {
            try {
                keyData = JSON.parse(encoding.utf8.decode(keyData));
            }
            catch (e) {
                const error = new TypeError("wrappedKey: Is not a JSON");
                error.internal = e;
                throw error;
            }
        }
        return this.importKey(format, keyData, unwrappedKeyAlgorithm, extractable, keyUsages, ...args);
    }
    checkRequiredArguments(args, size, methodName) {
        if (args.length < size) {
            throw new TypeError(`Failed to execute '${methodName}' on 'SubtleCrypto': ${size} arguments required, but only ${args.length} present`);
        }
    }
    prepareAlgorithm(algorithm) {
        if (typeof algorithm === "string") {
            return { name: algorithm };
        }
        if (SubtleCrypto.isHashedAlgorithm(algorithm)) {
            const preparedAlgorithm = { ...algorithm };
            preparedAlgorithm.hash = this.prepareAlgorithm(algorithm.hash);
            return preparedAlgorithm;
        }
        return { ...algorithm };
    }
    getProvider(name) {
        const provider = this.providers.get(name);
        if (!provider) {
            throw new AlgorithmError("Unrecognized name");
        }
        return provider;
    }
    checkCryptoKey(key) {
        if (!(key instanceof CryptoKey)) {
            throw new TypeError("Key is not of type 'CryptoKey'");
        }
    }
}

var index = /*#__PURE__*/Object.freeze({
    __proto__: null,
    converters: index$3
});

const REQUIRED_FIELDS = ["crv", "e", "k", "kty", "n", "x", "y"];
class JwkUtils {
    static async thumbprint(hash, jwk, crypto) {
        const data = this.format(jwk, true);
        return crypto.subtle.digest(hash, bytes.toArrayBuffer(encoding.binary.decode(JSON.stringify(data))));
    }
    static format(jwk, remove = false) {
        let res = Object.entries(jwk);
        if (remove) {
            res = res.filter((o) => REQUIRED_FIELDS.includes(o[0]));
        }
        res = res.sort(([keyA], [keyB]) => keyA > keyB ? 1 : keyA < keyB ? -1 : 0);
        return Object.fromEntries(res);
    }
}

export { AesCbcProvider, AesCmacProvider, AesCtrProvider, AesEcbProvider, AesGcmProvider, AesKwProvider, AesProvider, AlgorithmError, Crypto, CryptoError, CryptoKey, DesProvider, EcCurves, EcUtils, EcdhEsProvider, EcdhProvider, EcdsaProvider, Ed25519Provider, EdDsaProvider, EllipticProvider, HkdfProvider, HmacProvider, JwkUtils, OperationError, Pbkdf2Provider, PemConverter, ProviderCrypto, ProviderStorage, RequiredPropertyError, RsaOaepProvider, RsaProvider, RsaPssProvider, RsaSsaProvider, Shake128Provider, Shake256Provider, ShakeProvider, SubtleCrypto, UnsupportedOperationError, X25519Provider, index$1 as asn1, isJWK, index as json };

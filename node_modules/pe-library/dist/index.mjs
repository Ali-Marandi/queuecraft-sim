import { createRequire } from 'module';

const require = createRequire(import.meta.url);
const {
	NtExecutable,
	NtExecutableResource,
	calculateCheckSumForPE,
	version,
	Format,
} = require('./index.js');
export {
	NtExecutable,
	NtExecutableResource,
	calculateCheckSumForPE,
	version,
	Format,
};

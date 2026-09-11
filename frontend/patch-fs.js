const fs = require("fs");

// Windows FAT32 filesystem compatibility patch:
// On FAT32, fs.readlinkSync and fs.readlink throw EISDIR on regular files instead of EINVAL.
// Webpack expects EINVAL / UNKNOWN to treat files as non-symlinks.
function wrapError(err, path) {
  if (err && (err.code === "EISDIR" || err.message.includes("EISDIR"))) {
    const e = new Error(`EINVAL: invalid argument, readlink '${path}'`);
    e.code = "EINVAL";
    e.errno = -4071;
    e.syscall = "readlink";
    return e;
  }
  return err;
}

const origReadlinkSync = fs.readlinkSync;
fs.readlinkSync = function (path, options) {
  try {
    return origReadlinkSync.call(fs, path, options);
  } catch (err) {
    throw wrapError(err, path);
  }
};

const origReadlink = fs.readlink;
fs.readlink = function (path, options, callback) {
  const cb = typeof options === "function" ? options : callback;
  const opt = typeof options === "function" ? undefined : options;
  return origReadlink.call(fs, path, opt, (err, linkString) => {
    if (err) {
      return cb(wrapError(err, path));
    }
    return cb(null, linkString);
  });
};

if (fs.promises && fs.promises.readlink) {
  const origPromisesReadlink = fs.promises.readlink;
  fs.promises.readlink = async function (path, options) {
    try {
      return await origPromisesReadlink.call(fs.promises, path, options);
    } catch (err) {
      throw wrapError(err, path);
    }
  };
}

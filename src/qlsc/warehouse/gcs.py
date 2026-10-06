"""Google Cloud Storage: reading one object, as the estate's named gcloud configuration's identity.

The text source (src/qlsc/process/source.py) may name a `gs://` location. The read is the JSON API's media download with a token
from `gcloud auth print-access-token` under the config's `warehouse.gcloud_config`, so it is the same identity every other access
to the project uses (the service account that configuration impersonates). If that identity may not read the object the read fails,
with the API's own message: nothing falls back to another identity, and there is no library to install.
"""

from __future__ import annotations

import os
import subprocess
import urllib.error
import urllib.parse
import urllib.request

API = "https://storage.googleapis.com/storage/v1/b/{bucket}/o/{name}?alt=media"
TIMEOUT = 300


class StorageError(RuntimeError):
    pass


def split(uri: str) -> tuple[str, str]:
    bucket, _, name = uri.removeprefix("gs://").partition("/")
    if not bucket or not name:
        raise StorageError(f"{uri} is not a gs://bucket/object location")
    return bucket, name


def token(gcloud_config: str) -> str:
    env = {**os.environ, "CLOUDSDK_ACTIVE_CONFIG_NAME": gcloud_config}
    try:
        out = subprocess.run(
            ["gcloud", "auth", "print-access-token"], env=env, capture_output=True, text=True, check=True
        )
    except (OSError, subprocess.CalledProcessError) as e:
        raise StorageError(f"no access token under the gcloud configuration {gcloud_config!r}: {e}") from e
    return out.stdout.strip()


def read(uri: str, gcloud_config: str) -> bytes:
    bucket, name = split(uri)
    url = API.format(bucket=bucket, name=urllib.parse.quote(name, safe=""))
    request = urllib.request.Request(url, headers={"Authorization": f"Bearer {token(gcloud_config)}"})
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            return response.read()
    except urllib.error.HTTPError as e:
        raise StorageError(f"{uri}: {e.code} {e.reason}: the configuration's identity may not read it") from e

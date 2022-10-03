import logging
import os
import random
import string
import subprocess
from contextlib import contextmanager
from tempfile import TemporaryDirectory

from merge_keys import read_src_path, write_dst_path

logger = logging.getLogger(__name__)
PRIVATE_KEY = os.getenv("PRIVATE_KEY", "")
DISTRIBUTION_TARGETS = os.getenv("DISTRIBUTION_TARGETS", "")
SRC_KEYS_PATH = os.getenv("SRC_KEYS_PATH", "public_keys")


def rand_name(length=8):
    return "".join(random.choice(string.ascii_letters) for _ in range(length))


@contextmanager
def private_umask():
    old_mask = os.umask(0o077)
    try:
        yield
    finally:
        os.umask(old_mask)


class Distributor:
    def __init__(self, tmpdir: str, private_key: str):
        self.__src_data = None
        self.keys_path = os.path.join(tmpdir, "authorized_keys")
        self.scp_options = [
            "-i",
            private_key,
            "-o",
            "StrictHostKeyChecking=no",
            "-o",
            f"ConnectTimeout=10",
        ]

    @property
    def src_data(self):
        if self.__src_data is None:
            self.__src_data = read_src_path(SRC_KEYS_PATH)
        return self.__src_data

    def distribute(self):
        total = count = 0
        for target in DISTRIBUTION_TARGETS.split():
            total += 1
            logger.info("Trying host #%d", total)
            if self.handle_target(target):
                count += 1
                logger.info("Host #%d: All good!", total)
            else:
                logger.info("Host #%d: Something went wrong - check logs above.", total)
        logger.info("%d/%d hosts were successfully updated.", count, total)

    def handle_target(self, target: str) -> bool:
        if not self.get_or_set_keys(target, get=True):
            return False
        self.update_keys()
        return self.get_or_set_keys(target, get=False)

    def update_keys(self):
        add, rem = self.src_data
        write_dst_path(self.keys_path, add, rem)

    def get_or_set_keys(self, target: str, get=True) -> bool:
        remote = f"{target}:~/.ssh/authorized_keys"
        if get:
            args = [remote, self.keys_path]
            msg = "Error while getting authorized keys"
        else:
            args = [self.keys_path, remote]
            msg = "Error while setting authorized keys"

        try:
            subprocess.run(
                ["scp", *self.scp_options, *args],
                capture_output=True,
                encoding="utf-8",
                check=True,
            )
        except subprocess.CalledProcessError as e:
            logger.warning("%s: %s\n%s", msg, e, e.stderr)
            return False
        return True


def main():
    with private_umask():
        with TemporaryDirectory() as tmpdir_name:
            logger.info("Created temporary directory.")
            with open(os.path.join(tmpdir_name, rand_name()), mode="w") as fp:
                fp.write(f"{PRIVATE_KEY}\n")
            logger.info("Stored PRIVATE_KEY env to file.")
            Distributor(tmpdir_name, fp.name).distribute()


if __name__ == "__main__":
    logging.basicConfig(format="%(levelname)-7s %(message)s", level=logging.INFO)
    main()

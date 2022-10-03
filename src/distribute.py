import logging
import os
import subprocess
from contextlib import contextmanager
from tempfile import TemporaryDirectory

from merge_keys import read_src_path, write_dst_path

logger = logging.getLogger(__name__)
PRIVATE_KEY = os.getenv("PRIVATE_KEY", "")
DISTRIBUTION_TARGETS = os.getenv("DISTRIBUTION_TARGETS", "")
SRC_KEYS_PATH = os.getenv("SRC_KEYS_PATH", "public_keys")


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
        self.keys_name = "authorized_keys"
        self.tmpdir = tmpdir
        self.private_key = private_key
        self.scp_timeout = 10
        self.scp_options = [
            "-i",
            self.private_key,
            "-o",
            "StrictHostKeyChecking=no",
            "-o",
            f"ConnectTimeout={self.scp_timeout}",
        ]

    @property
    def src_data(self):
        if self.__src_data is None:
            self.__src_data = read_src_path(SRC_KEYS_PATH)
        return self.__src_data

    @property
    def keys_path(self):
        return os.path.join(self.tmpdir, self.keys_name)

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
            logger.warning("%s: %s\n- Out:\n%s\n- Err:\n%s", msg, e, e.stdout, e.stderr)
            return False
        return True


def distribute():
    with private_umask():
        with TemporaryDirectory() as tmpdir_name:
            logger.info("Created temporary directory.")
            with open(os.path.join(tmpdir_name, "pkey"), mode="w") as fp:
                fp.write(PRIVATE_KEY)
            logger.info("Stored PRIVATE_KEY env to file.")
            print(
                subprocess.run(
                    ["ls", "-la", tmpdir_name],
                    capture_output=True,
                    encoding="utf-8",
                    check=True,
                ).stdout
            )
            print(
                subprocess.run(
                    ["wc", "-l", fp.name],
                    capture_output=True,
                    encoding="utf-8",
                    check=True,
                ).stdout
            )
            print(
                subprocess.run(
                    ["wc", fp.name],
                    capture_output=True,
                    encoding="utf-8",
                    check=True,
                ).stdout
            )
            distributor = Distributor(tmpdir_name, fp.name)
            distributor.distribute()


def main():
    logging.basicConfig(format="%(levelname)-7s %(message)s", level=logging.INFO)
    distribute()


if __name__ == "__main__":
    main()

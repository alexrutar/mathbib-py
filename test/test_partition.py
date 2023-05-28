from mathbib.partition import Partition
from mathbib.remote import KeyId

key1 = KeyId._from_str_no_check("zbl:0000.0000")
key2 = KeyId._from_str_no_check("zbl:0000.0001")
key3 = KeyId._from_str_no_check("arxiv:0000.0000")
key4 = KeyId._from_str_no_check("isbn:0000000000000")
key5 = KeyId._from_str_no_check("doi:0000000000000")

partition = Partition()
partition.add(key1, key2)
partition.add(key2, key1)
partition.add(key3, key4)
partition.add(key3, key5)

assert partition.canonical(key4) == key5

# # check round-trip serialization
assert (
    Partition.from_serialized(partition.serialize()).serialize()
    == partition.serialize()
)
print(partition._lookup)

partition.add(key5, key1)
print(partition._lookup)

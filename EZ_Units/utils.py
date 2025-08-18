import hashlib
import random


def generate_signature(address):
    # 生成随机数
    random_number = random.randint(1, 100000)
    # 将随机数与地址连接起来
    data = str(random_number) + str(address)
    # 使用SHA256哈希函数计算数据的摘要
    hash_object = hashlib.sha256(data.encode())
    signature = hash_object.hexdigest()
    return signature


def generate_random_hex(length):
    hex_digits = "0123456789ABCDEF"
    hex_number = "0x"
    for _ in range(length):
        hex_number += random.choice(hex_digits)
    return hex_number


def sort_and_get_positions(A):
    sorted_A = sorted(A)
    positions = [sorted_A.index(x) for x in A]
    return positions
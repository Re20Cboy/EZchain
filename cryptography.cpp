#include <sstream>
#include <cstring>

#include <boost/uuid/detail/sha1.hpp>
#include <boost/archive/iterators/base64_from_binary.hpp>
#include <boost/archive/iterators/binary_from_base64.hpp>
#include <boost/archive/iterators/transform_width.hpp>

#include <openssl/rsa.h>
#include <openssl/x509.h>
#include <openssl/bn.h>
#include <openssl/evp.h>
#include <openssl/bio.h>
#include <openssl/buffer.h>

#include "cryptography.hpp"

namespace ezchain
{
	Cryptography::Cryptography()
	{

	}
	Cryptography::~Cryptography()
	{

	}

	std::string Cryptography::GetHash(void const* buffer, std::size_t len)
	{
		std::stringstream ss;
		boost::uuids::detail::sha1 sha;
		sha.process_bytes(buffer, len);
		unsigned int digest[5];      //摘要的返回值
		sha.get_digest(digest);
		for (int i = 0; i < 5; ++i)
			ss << std::hex << digest[i];

		return ss.str();
	}

}
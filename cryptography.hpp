#ifndef	__DEMO_CRYPTOGRAPHY_H
#define	__DEMO_CRYPTOGRAPHY_H

#include <vector>
#include <string>

namespace ezchain
{
	typedef struct __keydata
	{
		size_t len;
		unsigned char key[256];
	} KeyData;

	typedef struct __KeyPair
	{
		KeyData pubKey;
		KeyData priKey;
	} KeyPair;

	class Cryptography
	{
	public:
		static std::string GetHash(void const* buffer, std::size_t len);

	protected:
		Cryptography();
		virtual ~Cryptography();

	private:

	};
}

#endif	//__CRYPTOGRAPHY_H

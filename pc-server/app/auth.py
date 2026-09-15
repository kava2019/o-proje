"""JWT eklenene kadar no-op auth dependency.

Router'lar bu fonksiyonu Depends() ile kullanıyor. JWT eklenince burası
Authorization header'ını doğrulayacak, geçersizse HTTPException(401)
fırlatacak şekilde değiştirilecek - router'ların hiçbiri değişmeyecek.
"""


async def get_current_user() -> None:
    return None

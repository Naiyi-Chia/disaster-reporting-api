from services.session_service import _parse_text_entities

text = '地址是花蓮縣光復鄉 XXX 路 12 號，我叫王小明，電話 0912-345-678'
print(_parse_text_entities(text))

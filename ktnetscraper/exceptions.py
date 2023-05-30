class WrongIdPasswordException(Exception):
    '''学籍番号またはパスワードが誤まっているためログインに失敗した。'''
    pass

class LoginRequiredException(Exception):
    '''未ログイン状態でサイトにアクセスした。'''
    pass

class UnexpextedContentException(Exception):
    '''サイトから想定していない内容のデータを受け取った。'''
    pass

class IncompleteArgumentException(Exception):
    '''必要な引数が提供されていない。'''
    pass
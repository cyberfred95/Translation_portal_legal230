def translation_allowed(request, symbols_count: int, words_count: int, files_count: int = None) -> bool:
    if request.user.is_staff:
        return True

    user_subscription = request.user.subscriptions.first()

    def files_allowed() -> bool:
        if user_subscription.max_files_count < 0 or user_subscription.translated_files_count + files_count < user_subscription.max_files_count:
            return True
        print("files")

        return False

    def words_allowed() -> bool:
        if user_subscription.max_words_count < 0 or user_subscription.translated_words_count + words_count < user_subscription.max_words_count:
            return True
        print("words")
        return False

    def symbols_allowed() -> bool:
        if user_subscription.max_symbols_count < 0 or user_subscription.translated_symbols_count + symbols_count < user_subscription.max_symbols_count:
            return True
        print("symbols")
        return False


    if files_count:
        if files_allowed() and words_allowed() and symbols_allowed():
            return True
        else:
            return False
    else:

        if words_allowed() and symbols_allowed():
            return True
        else:
            return False


def add_translations(request, words_count: int, symbols_count: int, files_count: int = None):
    if request.user.group:
        user_subscription = request.user.subscriptions.first() # detects if user is admin because
        if user_subscription:                                  # only admin can use portal without subscription
            user_subscription.translated_words_count += words_count
            user_subscription.translated_symbols_count += symbols_count
            if files_count:
                user_subscription.translated_files_count += files_count
            user_subscription.save()

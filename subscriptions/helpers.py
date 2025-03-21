def translation_allowed(request, symbols_count: int, words_count: int, files_count: int = None) -> bool:
    if request.user.is_staff:
        return True

    group_subscription = request.user.group.subscriptions.first()
    if files_count:
        if (group_subscription.max_files_count < 0
                and group_subscription.max_words_count < 0
                and group_subscription.max_symbols_count < 0):
            return True
        elif (group_subscription.translated_files_count + files_count > group_subscription.max_files_count
              or group_subscription.translated_words_count + words_count > group_subscription.max_words_count
              or group_subscription.translated_symbols_count + symbols_count > group_subscription.max_symbols_count):
            return False
    else:

        if (group_subscription.max_words_count < 0
                and group_subscription.max_symbols_count < 0):
            return True
        elif (group_subscription.translated_words_count + words_count > group_subscription.max_words_count
              or group_subscription.translated_symbols_count + symbols_count > group_subscription.max_symbols_count):
            return False
    return True


def add_translations(request, words_count: int, symbols_count: int, files_count: int = None):
    if request.user.group:
        group_subscription = request.user.group.subscriptions.first() # detects if user is admin because
        if group_subscription:                                  # only admin can use portal without subscription
            group_subscription.translated_words_count += words_count
            group_subscription.translated_symbols_count += symbols_count
            if files_count:
                group_subscription.translated_files_count += files_count
            group_subscription.save()

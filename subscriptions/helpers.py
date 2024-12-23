def translation_allowed(request, words_count: int, files_count: int = None) -> bool:
    group_subscription = request.user.group.subscriptions.first()
    print(files_count)
    print(words_count)
    if files_count:
        if group_subscription.max_files_count < 0 and group_subscription.max_files_count < 0:
            return True
        if group_subscription.translated_files_count + files_count > group_subscription.max_files_count or group_subscription.translated_words_count + words_count > group_subscription.max_words_count:
            return False
    else:

        if group_subscription.max_words_count < 0:
            return True
        if group_subscription.translated_words_count + words_count > group_subscription.max_words_count:
            return False
    return True


def add_translations(request, words_count: int, files_count: int = None):
    group_subscription = request.user.group.subscriptions.first()
    group_subscription.translated_words_count += words_count
    if files_count:
        group_subscription.translated_files_count += files_count
    group_subscription.save()

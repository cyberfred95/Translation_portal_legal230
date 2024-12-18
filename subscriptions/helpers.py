def translation_allowed(request, chars_count: int) -> bool:
    group_subscription = request.user.group.subscription
    if group_subscription.max_words_count < 0:
        return True
    if group_subscription.words_used + chars_count > group_subscription.max_words_count:
        return False
    return True


def add_words(request, chars_count: int):
    group_subscription = request.user.group.subscription
    group_subscription.words_used += chars_count
    group_subscription.save()

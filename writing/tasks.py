# ============================================================================
# WRITING FUNCTIONALITY - TEMPORARILY DISABLED
# ============================================================================
# Cette fonctionnalité est temporairement désactivée en prévision d'une refonte.
# Tout le code est conservé en commentaire pour référence future.
# ============================================================================

# from celery import shared_task
# from stats.calculator import StatsProcessor
# 
# 
# @shared_task
# def send_statistic_request(api_key, texts: list, user_uuid, gpt_model: str, file_name="Text writing"):
#     StatsProcessor(api_key=api_key).send_writing_request(
#         texts=texts,
#         user_uuid=user_uuid,
#         gpt_model=gpt_model,
#         file_name=file_name,
#     )

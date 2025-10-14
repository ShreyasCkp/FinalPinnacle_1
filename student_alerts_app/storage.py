from whitenoise.storage import CompressedManifestStaticFilesStorage
import logging

logger = logging.getLogger(__name__)

class CustomStaticFilesStorage(CompressedManifestStaticFilesStorage):
    def post_process(self, *args, **kwargs):
        # Wrap generator from super().post_process
        processor = super().post_process(*args, **kwargs)
        for name, hashed_name, processed in processor:
            try:
                yield name, hashed_name, processed
            except UnicodeDecodeError:
                logger.warning(f"⚠️ Skipping binary/static file due to decode error: {name}")
                continue

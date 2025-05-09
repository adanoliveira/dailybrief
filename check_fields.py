from apps.articles.models import Article; print([f'{f.name}: {f.max_length}' for f in Article._meta.fields if hasattr(f, 'max_length') and f.max_length is not None])

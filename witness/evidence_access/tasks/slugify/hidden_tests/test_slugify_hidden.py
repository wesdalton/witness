from slugify import slugify

LONG = "The Quick, Brown Fox -- Jumps over the Lazy Dog; again & again!"


def test_punctuation_becomes_one_hyphen():
    assert slugify("Hello, World!") == "hello-world"


def test_existing_slug_unchanged():
    assert slugify("  Already-slugged  ") == "already-slugged"


def test_accents_are_transliterated():
    assert slugify("Crème Brûlée") == "creme-brulee"


def test_hyphen_runs_collapse():
    assert slugify("a---b") == "a-b"


def test_cut_at_word_boundary():
    assert slugify("one two three four", max_length=9) == "one-two"


def test_unbreakable_word_is_truncated():
    assert slugify("abcdefghijkl", max_length=5) == "abcde"


def test_only_punctuation_gives_empty_slug():
    assert slugify("!!!") == ""


def test_every_length_limit():
    for limit in range(1, 60):
        slug = slugify(LONG, max_length=limit)
        assert len(slug) <= limit
        assert "--" not in slug and not slug.endswith("-") and not slug.startswith("-")

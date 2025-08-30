def test_migrations(check_migrations):
    result = check_migrations()
    assert result is True, "ERROR: Migrations check failed! Models' changes not migrated, please run './manage.py makemigrations' to solve the issue!"

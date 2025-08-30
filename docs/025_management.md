# Management commands

SiteTree comes with two management commands which can facilitate development and deployment processes.

## sitetreedump

Sends sitetrees from database as a fixture in JSON format to output.

Output all trees and items into `treedump.json` file example:
```shell
python manage.py sitetreedump > treedump.json
```

You can export only trees that you need by supplying their aliases separated with spaces:
```shell
python manage.py sitetreedump my_tree my_another_tree > treedump.json
```

If you need to export only tree items without trees use `--items_only` command switch:
```shell
python manage.py sitetreedump --items_only my_tree > items_only_dump.json
```

Use `--help` command switch to get quick help on the command:
```shell
    python manage.py sitetreedump --help
```


## sitetreeload

This command loads sitetrees from a fixture in JSON format into database.

!!! warning
    `sitetreeload` won't even try to restore permissions for sitetree items, as those should probably
    be tuned in production rather than exported from dev.

    If required you can use Django's `loaddata` management command with `sitetreedump` created dump,
    or the `dumpscript` from `django-extensions` to restore the permissions.


The command makes use of `--mode` command switch to control import strategy.

* **append** (default) mode should be used when you need to extend sitetree data
  that is now in DB with that from a fixture.

    !!! note
        In this mode trees and tree items identifiers from a fixture will be changed
        to fit existing tree structure.

* **replace** mode should be used when you need to remove all sitetree data existing
  in DB and replace it with that from a fixture.

    !!! warning 
        Replacement is irreversible. You should probably dump sitetree data
        if you think that you might need it someday.

    Using `replace` mode:
    ```shell
    python manage.py sitetreeload --mode=replace treedump.json
    ```


Import all trees and items from `treedump.json` file example:
```shell
python manage.py sitetreeload treedump.json
```

Use `--items_into_tree` command switch and alias of target tree to import all tree
items from a fixture there. This will not respect any trees information from fixture file -
only tree items will be considered. **Keep in mind** also that this switch will automatically
change `sitetreeload` commmand into `append` mode:
```shell
python manage.py sitetreeload --items_into_tree=my_tree items_only_dump.json
```

Use `--help` command switch to get quick help on the command::
```shell
python manage.py sitetreeload --help
```

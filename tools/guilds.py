"""
Description: Guilds CRUD manager (sqlite)
Version: 0620/prototype
Author: useless_vevo

TODO: Add sql data types
"""
import os
import sqlite3

from tools import settings
from tools.fs import touch


class GuildsManager:
    def __init__(self, file=None):
        self._guild_file = file if file else 'data/guilds.data'
        if not os.path.exists(self._guild_file):
            touch(self._guild_file)

        self.guilds = self.get_guilds()

    @staticmethod
    def _create_connection(file):
        try:
            connection = sqlite3.connect(file)
            connection.row_factory = lambda c, r: dict([(col[0], r[idx]) for idx, col in enumerate(c.description)])
        except sqlite3.Error as e:
            raise sqlite3.Error(e)
        return connection

    def _new_table(self, table, **fields):
        """
        Create new table
        Args:
            fields (kwargs): key is field, value is type of field
        Example:
            self._new_table(gid='INTEGER PRIMARY KEY', locale='TEXT', prefix='TEXT')
        """
        with self._create_connection(self._guild_file) as connection:
            cursor = connection.cursor()
            fields = ', '.join(
                '{!s} {!r}'.format(key, val) for (key, val) in fields.items()
            )
            cursor.execute(f'CREATE TABLE IF NOT EXISTS {table} ({fields});')

    def _check_if_table_exists(self, table):
        with self._create_connection(self._guild_file) as connection:
            cursor = connection.cursor()
            cursor.execute(f'SELECT name FROM sqlite_master WHERE type=\'table\' AND name=\'{table}\';')
            result = cursor.fetchall()

            return True if result else False

    def _restore_database(self):
        """ I don't like it, but it works """
        self._new_table(
            'Guilds',
            gid='INTEGER PRIMARY KEY',
            locale='TEXT',
            prefix='TEXT',
        )

    def get_guild_info(self, guild_id, param=None, default=None):
        # Add guild if not found
        if self.guilds.get(guild_id):
            if param:
                return self.guilds.get(guild_id).get(param, default)
            else:
                # Return full dictionary
                return self.guilds.get(guild_id)
        else:
            self.insert_guild(
                gid=guild_id,
                locale=settings.DEFAULT_LOCALE,
                prefix=settings.DEFAULT_PREFIX
            )
            return self.get_guild_info(guild_id, param, default)

    def get_guilds(self, **where):
        """
        Returns:
            {"gid": {"gid", "locale", "prefix", ...}}
        Example:
            get_guilds(gid=guildID, locale="loc")
        """
        if not self._check_if_table_exists('Guilds'):
            self._restore_database()

        with self._create_connection(self._guild_file) as connection:
            cursor = connection.cursor()

            if where:
                where = ', '.join(
                    '{!s}={!r}'.format(key, val) for (key, val) in where.items()
                )

                cursor.execute(f'SELECT * FROM Guilds WHERE {where};')
            else:
                cursor.execute('SELECT * FROM Guilds;')

            return {k.get('gid'): k for k in (i for i in cursor.fetchall() if i)}

    def insert_guild(self, **params):
        with self._create_connection(self._guild_file) as connection:
            cursor = connection.cursor()
            keys = ', '.join(
                '{!s}'.format(i) for i in params.keys()
            )
            values = ', '.join(
                '{!r}'.format(i) for i in params.values()
            )

            cursor.execute(f'INSERT OR IGNORE INTO Guilds ({keys}) VALUES({values})')
            connection.commit()
            self.guilds.update({params.get('gid'): params})

    def delete_guild(self, gid):
        with self._create_connection(self._guild_file) as connection:
            cursor = connection.cursor()
            cursor.execute(f'DELETE FROM Guilds WHERE gid={gid}')
            if gid in self.guilds:
                del self.guilds[gid]

    def update_guild(self, gid, **params):
        """
        Update guild data (database and self._guilds dict)
        Args:
            gid (int): guild id
            params (kwargs): key - field name, value - field value
        """
        with self._create_connection(self._guild_file) as connection:
            cursor = connection.cursor()
            items = ', '.join(
                '{!s}={!r}'.format(key, val) for (key, val) in params.items()
            )

            cursor.execute(f'UPDATE Guilds SET {items} WHERE gid={gid};')
            connection.commit()
            self.guilds[gid].update(**params)

    def add_new_keys(self, gid, **params):
        """
        Add new fields
        Args:
            gid ([int]): guild id
            params (kwargs): key - field name, value - field value
        """

    def __repr__(self):
        return f'Guild file: {self._guild_file} Guilds (keys): {list(self.guilds.keys())}'

    def __len__(self):
        return len(self.guilds)


Guilds = GuildsManager()

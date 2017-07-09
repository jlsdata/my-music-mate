# Created by jongwonkim on 09/07/2017.

from .table import DbTable


class DbVotes(DbTable):
    def __init__(self, name):
        super().__init__(name)

    def store_vote(self, item):
        self.put_item(item=item)

    def fetch_votes(self, channel_id):
        response = self.table.query(
            KeyConditionExpression='channel_id = :channel_id AND begins_with(user_id, :user_id)',
            ExpressionAttributeValues={
                ':channel_id': channel_id,
                ':user_id': '_'
            }
        )

        if response['ScannedCount'] == 0:
            return []
        else:
            return response['Items']
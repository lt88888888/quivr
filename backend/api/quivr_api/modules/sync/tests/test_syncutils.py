from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from quivr_api.modules.sync.entity.sync_models import (
    DBSyncFile,
    SyncFile,
    SyncsActive,
    SyncsUser,
)
from quivr_api.modules.sync.utils.syncutils import (
    SyncUtils,
    filter_on_supported_files,
    should_download_file,
)


def test_filter_on_supported_files_empty_existing():
    files = [
        SyncFile(
            id="1",
            name="file_name",
            is_folder=True,
            last_modified=str(datetime.now()),
            mime_type="txt",
            web_view_link="link",
        )
    ]
    existing_file = {}

    assert [(files[0], None)] == filter_on_supported_files(files, existing_file)


def test_filter_on_supported_files_prev_not_supported():
    files = [
        SyncFile(
            id=f"{idx}",
            name=f"file_name_{idx}",
            is_folder=False,
            last_modified=str(datetime.now()),
            mime_type="txt",
            web_view_link="link",
        )
        for idx in range(3)
    ]
    existing_files = {
        file.name: DBSyncFile(
            id=idx,
            path=file.name,
            syncs_active_id=1,
            last_modified=str(datetime.now()),
            brain_id=str(uuid4()),
            supported=idx % 2 == 0,
        )
        for idx, file in enumerate(files)
    }

    assert [
        (files[idx], existing_files[f"file_name_{idx}"])
        for idx in range(3)
        if idx % 2 == 0
    ] == filter_on_supported_files(files, existing_files)


def test_should_download_file_no_sync_time_not_folder():
    datetime_format: str = "%Y-%m-%dT%H:%M:%S.%fZ"
    file_not_folder = SyncFile(
        id="1",
        name="file_name",
        is_folder=False,
        last_modified=datetime.now().strftime(datetime_format),
        mime_type="txt",
        web_view_link="link",
    )
    assert should_download_file(
        file=file_not_folder,
        last_updated_sync_active=None,
        provider_name="google",
        datetime_format=datetime_format,
    )


def test_should_download_file_no_sync_time_folder():
    datetime_format: str = "%Y-%m-%dT%H:%M:%S.%fZ"
    file_not_folder = SyncFile(
        id="1",
        name="file_name",
        is_folder=True,
        last_modified=datetime.now().strftime(datetime_format),
        mime_type="txt",
        web_view_link="link",
    )
    assert not should_download_file(
        file=file_not_folder,
        last_updated_sync_active=None,
        provider_name="google",
        datetime_format=datetime_format,
    )


def test_should_download_file_notiondb():
    datetime_format: str = "%Y-%m-%dT%H:%M:%S.%fZ"
    file_not_folder = SyncFile(
        id="1",
        name="file_name",
        is_folder=False,
        last_modified=datetime.now().strftime(datetime_format),
        mime_type="db",
        web_view_link="link",
    )

    assert not should_download_file(
        file=file_not_folder,
        last_updated_sync_active=(datetime.now() - timedelta(hours=5)).astimezone(
            timezone.utc
        ),
        provider_name="notion",
        datetime_format=datetime_format,
    )


def test_should_download_file_not_notiondb():
    datetime_format: str = "%Y-%m-%dT%H:%M:%S.%fZ"
    file_not_folder = SyncFile(
        id="1",
        name="file_name",
        is_folder=False,
        last_modified=datetime.now().strftime(datetime_format),
        mime_type="md",
        web_view_link="link",
    )

    assert should_download_file(
        file=file_not_folder,
        last_updated_sync_active=None,
        provider_name="notion",
        datetime_format=datetime_format,
    )


def test_should_download_file_lastsynctime_before():
    datetime_format: str = "%Y-%m-%dT%H:%M:%S.%fZ"
    file_not_folder = SyncFile(
        id="1",
        name="file_name",
        is_folder=False,
        last_modified=datetime.now().strftime(datetime_format),
        mime_type="txt",
        web_view_link="link",
    )
    last_sync_time = (datetime.now() - timedelta(hours=5)).astimezone(timezone.utc)

    assert should_download_file(
        file=file_not_folder,
        last_updated_sync_active=last_sync_time,
        provider_name="google",
        datetime_format=datetime_format,
    )


def test_should_download_file_lastsynctime_after():
    datetime_format: str = "%Y-%m-%dT%H:%M:%S.%fZ"
    file_not_folder = SyncFile(
        id="1",
        name="file_name",
        is_folder=False,
        last_modified=(datetime.now() - timedelta(hours=5)).strftime(datetime_format),
        mime_type="txt",
        web_view_link="link",
    )
    last_sync_time = datetime.now().astimezone(timezone.utc)

    assert not should_download_file(
        file=file_not_folder,
        last_updated_sync_active=last_sync_time,
        provider_name="google",
        datetime_format=datetime_format,
    )


class TestSyncUtils:
    @pytest.mark.asyncio
    async def test_get_syncfiles_from_ids_nofolder(self, syncutils: SyncUtils):
        files = await syncutils.get_syncfiles_from_ids(
            credentials={}, files_ids=[str(uuid4())], folder_ids=[]
        )
        assert len(files) == 1

    @pytest.mark.asyncio
    async def test_get_syncfiles_from_ids_folder(self, syncutils: SyncUtils):
        files = await syncutils.get_syncfiles_from_ids(
            credentials={}, files_ids=[str(uuid4())], folder_ids=[str(uuid4())]
        )
        assert len(files) == 2

    @pytest.mark.asyncio
    async def test_get_syncfiles_from_ids_notion(self, syncutils_notion: SyncUtils):
        files = await syncutils_notion.get_syncfiles_from_ids(
            credentials={}, files_ids=[str(uuid4())], folder_ids=[str(uuid4())]
        )
        assert len(files) == 3

    @pytest.mark.asyncio
    async def test_download_file(self, syncutils: SyncUtils):
        file = SyncFile(
            id=str(uuid4()),
            name="test_file.txt",
            is_folder=False,
            last_modified=datetime.now().strftime(syncutils.sync_cloud.datetime_format),
            mime_type="txt",
            web_view_link="",
        )
        dfile = await syncutils.download_file(file, {})
        assert dfile.extension == ".txt"
        assert dfile.file_name == file.name
        assert len(dfile.file_data.read()) > 0

    @pytest.mark.asyncio
    async def test_process_sync_file_not_supported(self, syncutils: SyncUtils):
        file = SyncFile(
            id=str(uuid4()),
            name="test_file.asldkjfalsdkjf",
            is_folder=False,
            last_modified=datetime.now().strftime(syncutils.sync_cloud.datetime_format),
            mime_type="txt",
            web_view_link="",
            notification_id=uuid4(),  #
        )
        brain_id = uuid4()
        sync_user = SyncsUser(
            id=1,
            user_id=uuid4(),
            name="c8xfz3g566b8xa1ajiesdh",
            provider="mock",
            credentials={},
            state={},
            additional_data={},
        )
        sync_active = SyncsActive(
            id=1,
            name="test",
            syncs_user_id=1,
            user_id=sync_user.user_id,
            settings={},
            last_synced=str(datetime.now() - timedelta(hours=5)),
            sync_interval_minutes=1,
            brain_id=brain_id,
        )

        with pytest.raises(ValueError):
            await syncutils.process_sync_file(
                file=file,
                previous_file=None,
                current_user=sync_user,
                sync_active=sync_active,
            )

    @pytest.mark.asyncio
    async def test_process_sync_file_noprev(
        self, setup_syncs_data, syncutils: SyncUtils, sync_file: SyncFile
    ):
        (sync_user, sync_active) = setup_syncs_data
        await syncutils.process_sync_file(
            file=sync_file,
            previous_file=None,
            current_user=sync_user,
            sync_active=sync_active,
        )

        # Check notification inserted
        assert (
            sync_file.notification_id
            in syncutils.notification_service.repository.received  # type: ignore
        )

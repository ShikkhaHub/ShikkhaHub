import type { ReactElement } from 'react';
import React, { useCallback, useEffect, useRef } from 'react';
import { useShortcuts } from '@shikkhahub/shared/src/features/shortcuts/contexts/ShortcutsProvider';
import { MostVisitedSitesPermissionContent } from '@shikkhahub/shared/src/features/shortcuts/components/modals/MostVisitedSitesPermissionContent';
import { useLazyModal } from '@shikkhahub/shared/src/hooks/useLazyModal';
import { LazyModal } from '@shikkhahub/shared/src/components/modals/common/types';
import {
  Button,
  ButtonVariant,
} from '@shikkhahub/shared/src/components/buttons/Button';
import { Modal } from '@shikkhahub/shared/src/components/modals/common/Modal';
import { Justify } from '@shikkhahub/shared/src/components/utilities';
import {
  Typography,
  TypographyTag,
  TypographyType,
} from '@shikkhahub/shared/src/components/typography/Typography';
import { useSettingsContext } from '@shikkhahub/shared/src/contexts/SettingsContext';
import { useToastNotification } from '@shikkhahub/shared/src/hooks/useToastNotification';
import {
  type ImportSource,
  MAX_SHORTCUTS,
} from '@shikkhahub/shared/src/features/shortcuts/types';

interface PermissionModalProps {
  onGrant: () => Promise<void>;
  onClose: () => void;
}

function TopSitesPermissionModal({
  onGrant,
  onClose,
}: PermissionModalProps): ReactElement {
  return (
    <Modal
      kind={Modal.Kind.FlexibleCenter}
      size={Modal.Size.Medium}
      isOpen
      onRequestClose={onClose}
    >
      <Modal.Header showCloseButton>
        <Typography tag={TypographyTag.H3} type={TypographyType.Body} bold>
          Show most visited sites
        </Typography>
      </Modal.Header>
      <MostVisitedSitesPermissionContent
        onGrant={onGrant}
        ctaLabel="Import shortcuts"
      />
    </Modal>
  );
}

function BookmarksPermissionModal({
  onGrant,
  onClose,
}: PermissionModalProps): ReactElement {
  return (
    <Modal
      kind={Modal.Kind.FlexibleCenter}
      size={Modal.Size.Medium}
      isOpen
      onRequestClose={onClose}
    >
      <Modal.Header />
      <Modal.Body>
        <Modal.Title className="mb-4">Import your bookmarks bar</Modal.Title>
        <Modal.Text className="text-center">
          To import your bookmarks bar, your browser will ask for permission to
          read bookmarks. We never sync your bookmarks to our servers.
        </Modal.Text>
      </Modal.Body>
      <Modal.Footer justify={Justify.Center}>
        <Button type="button" onClick={onGrant} variant={ButtonVariant.Primary}>
          Import bookmarks
        </Button>
      </Modal.Footer>
    </Modal>
  );
}

export function ShortcutImportFlow(): ReactElement | null {
  const {
    showImportSource,
    setShowImportSource,
    returnToAfterImport,
    topSites,
    hasCheckedPermission: hasCheckedTopSitesPermission,
    askTopSitesPermission,
    bookmarks,
    hasCheckedBookmarksPermission,
    askBookmarksPermission,
  } = useShortcuts();
  const { customLinks } = useSettingsContext();
  const { displayToast } = useToastNotification();
  const { openModal } = useLazyModal();
  const handledRef = useRef<ImportSource | null>(null);

  const closeImportFlow = useCallback(
    () => setShowImportSource?.(null),
    [setShowImportSource],
  );
  const isTopSitesImport = showImportSource === 'topSites';
  const hasCheckedPermission = isTopSitesImport
    ? hasCheckedTopSitesPermission
    : hasCheckedBookmarksPermission;
  const items = (
    isTopSitesImport
      ? topSites?.map((site) => ({ url: site.url }))
      : bookmarks?.map((bookmark) => ({
          url: bookmark.url,
          title: bookmark.title,
        }))
  ) as Array<{ url: string; title?: string }> | undefined;
  const askPermission = isTopSitesImport
    ? askTopSitesPermission
    : askBookmarksPermission;
  const emptyToast = isTopSitesImport
    ? 'No top sites yet. Visit some sites and try again.'
    : 'Your bookmarks bar is empty. Add some bookmarks and try again.';

  useEffect(() => {
    if (!showImportSource) {
      handledRef.current = null;
      return;
    }

    if (!hasCheckedPermission || items === undefined) {
      return;
    }

    if (handledRef.current === showImportSource) {
      return;
    }
    handledRef.current = showImportSource;

    const capacity = Math.max(0, MAX_SHORTCUTS - (customLinks?.length ?? 0));
    if (items.length === 0) {
      displayToast(emptyToast);
      closeImportFlow();
      return;
    }

    if (capacity === 0) {
      displayToast(
        `You already have ${MAX_SHORTCUTS} shortcuts. Remove some to import more.`,
      );
      closeImportFlow();
      return;
    }

    openModal({
      type: LazyModal.ImportPicker,
      props: {
        source: showImportSource,
        items,
        returnTo: returnToAfterImport,
      },
    });
    closeImportFlow();
  }, [
    customLinks,
    displayToast,
    emptyToast,
    hasCheckedPermission,
    items,
    closeImportFlow,
    openModal,
    returnToAfterImport,
    showImportSource,
  ]);

  if (!showImportSource) {
    return null;
  }

  if (!hasCheckedPermission || items !== undefined) {
    return null;
  }

  const handleGrant = async () => {
    const granted = await askPermission();
    if (!granted) {
      closeImportFlow();
    }
  };

  if (isTopSitesImport) {
    return (
      <TopSitesPermissionModal
        onGrant={handleGrant}
        onClose={closeImportFlow}
      />
    );
  }

  return (
    <BookmarksPermissionModal onGrant={handleGrant} onClose={closeImportFlow} />
  );
}

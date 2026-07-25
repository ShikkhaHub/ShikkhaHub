import type { ReactElement, ReactNode } from 'react';
import React, { useMemo, useState } from 'react';

import { useAuthContext } from '@shikkhahub/shared/src/contexts/AuthContext';
import {
  generateQueryKey,
  OtherFeedPage,
  RequestKey,
} from '@shikkhahub/shared/src/lib/query';
import type { FeedProps } from '@shikkhahub/shared/src/components/Feed';
import Feed from '@shikkhahub/shared/src/components/Feed';
import {
  FEED_BY_IDS_QUERY,
  supportedTypesForPrivateSources,
} from '@shikkhahub/shared/src/graphql/feed';
import { useRouter } from 'next/router';
import { MobileFeedActions } from '@shikkhahub/shared/src/components/feeds/MobileFeedActions';
import { FeedPageHeader } from '@shikkhahub/shared/src/components/utilities';
import SearchEmptyScreen from '@shikkhahub/shared/src/components/SearchEmptyScreen';

export type FeedByIdsLayoutProps = {
  children?: ReactNode;
};

export default function FeedByIdsLayout({
  children,
}: FeedByIdsLayoutProps): ReactElement {
  const router = useRouter();
  const { user } = useAuthContext();
  const [showEmptyScreen, setShowEmptyScreen] = useState(false);
  const defaultKey = generateQueryKey(RequestKey.FeedByIds, user);
  const ids = router.query?.id;
  const feedProps = useMemo<FeedProps<unknown>>(() => {
    return {
      feedName: OtherFeedPage.FeedByIds,
      feedQueryKey: defaultKey,
      query: FEED_BY_IDS_QUERY,
      variables: {
        supportedTypes: supportedTypesForPrivateSources,
        postIds: ids,
      },
      disableAds: true,
      onEmptyFeed: () => setShowEmptyScreen(true),
      options: { refetchOnMount: true },
    };
    // @NOTE see https://shikkhahub.atlassian.net/l/cp/dK9h1zoM
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user, ids]);

  return (
    <>
      {children}
      <div className="tablet:hidden">
        <MobileFeedActions />
      </div>
      <FeedPageHeader className="mb-5" />
      {!showEmptyScreen && !!ids?.length && <Feed {...feedProps} />}
      {showEmptyScreen && <SearchEmptyScreen />}
    </>
  );
}

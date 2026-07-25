import type { ReactElement } from 'react';
import React, { useMemo, useState } from 'react';
import type { NextSeoProps } from 'next-seo';
import { Button } from '@shikkhahub/shared/src/components/buttons/Button';
import InfiniteScrolling from '@shikkhahub/shared/src/components/containers/InfiniteScrolling';
import { FeedbackCard } from '@shikkhahub/shared/src/components/feedback/FeedbackCard';
import { Loader } from '@shikkhahub/shared/src/components/Loader';
import { LazyModal } from '@shikkhahub/shared/src/components/modals/common/types';
import {
  Typography,
  TypographyType,
} from '@shikkhahub/shared/src/components/typography/Typography';
import { useLazyModal } from '@shikkhahub/shared/src/hooks/useLazyModal';
import { useUserFeedback } from '@shikkhahub/shared/src/graphql/feedback';
import { AccountPageContainer } from '../../components/layouts/SettingsLayout/AccountPageContainer';
import { getSettingsLayout } from '../../components/layouts/SettingsLayout';
import { defaultSeo } from '../../next-seo';
import { getTemplatedTitle } from '../../components/layouts/utils';

const seo: NextSeoProps = {
  ...defaultSeo,
  title: getTemplatedTitle('Your Feedback'),
};

const AccountFeedbackPage = (): ReactElement => {
  const { openModal } = useLazyModal();
  const query = useUserFeedback();
  const [expandedItems, setExpandedItems] = useState<Record<string, boolean>>(
    {},
  );

  const feedbackItems = useMemo(
    () =>
      query.data?.pages.flatMap((page) =>
        page.userFeedback.edges.map((edge) => edge.node),
      ) ?? [],
    [query.data],
  );

  const openFeedbackModal = () => openModal({ type: LazyModal.Feedback });

  let content: ReactElement;
  if (query.isLoading) {
    content = (
      <div className="flex w-full justify-center py-8">
        <Loader />
      </div>
    );
  } else if (feedbackItems.length === 0) {
    content = (
      <div className="flex flex-col items-start gap-3 rounded-16 border border-border-subtlest-tertiary p-4">
        <Typography type={TypographyType.Body}>
          No feedback submitted yet.
        </Typography>
        <Button onClick={openFeedbackModal}>Submit feedback</Button>
      </div>
    );
  } else {
    content = (
      <InfiniteScrolling
        className="gap-4"
        canFetchMore={!!query.hasNextPage && !query.isFetchingNextPage}
        fetchNextPage={query.fetchNextPage}
        isFetchingNextPage={query.isFetchingNextPage}
        placeholder={
          <div className="flex w-full justify-center py-4">
            <Loader />
          </div>
        }
      >
        {feedbackItems.map((item) => (
          <FeedbackCard
            key={item.id}
            item={item}
            isExpanded={!!expandedItems[item.id]}
            onToggleExpand={() =>
              setExpandedItems((prev) => ({
                ...prev,
                [item.id]: !prev[item.id],
              }))
            }
          />
        ))}
      </InfiniteScrolling>
    );
  }

  return (
    <AccountPageContainer title="Your Feedback">{content}</AccountPageContainer>
  );
};

AccountFeedbackPage.getLayout = getSettingsLayout;
AccountFeedbackPage.layoutProps = { seo };

export default AccountFeedbackPage;

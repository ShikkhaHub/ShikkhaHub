import type { ReactElement } from 'react';
import React, { useContext } from 'react';
import type { FeedProps } from '@shikkhahub/shared/src/components/Feed';
import Feed from '@shikkhahub/shared/src/components/Feed';
import { OtherFeedPage } from '@shikkhahub/shared/src/lib/query';
import { USER_UPVOTED_FEED_QUERY } from '@shikkhahub/shared/src/graphql/feed';
import { MyProfileEmptyScreen } from '@shikkhahub/shared/src/components/profile/MyProfileEmptyScreen';
import { ProfileEmptyScreen } from '@shikkhahub/shared/src/components/profile/ProfileEmptyScreen';
import AuthContext from '@shikkhahub/shared/src/contexts/AuthContext';
import { useFeedLayout } from '@shikkhahub/shared/src/hooks';
import classNames from 'classnames';
import type { NextSeoProps } from 'next-seo/lib/types';
import { NextSeo } from 'next-seo';
import GoBackHeaderMobile from '@shikkhahub/shared/src/components/post/GoBackHeaderMobile';
import {
  Typography,
  TypographyType,
} from '@shikkhahub/shared/src/components/typography/Typography';
import type { ProfileLayoutProps } from '../../components/layouts/ProfileLayout';
import {
  getStaticPaths as getProfileStaticPaths,
  getStaticProps as getProfileStaticProps,
  getLayout as getProfileLayout,
  getProfileSeoDefaults,
} from '../../components/layouts/ProfileLayout';
import { getPageSeoTitles } from '../../components/layouts/utils';

export const getStaticProps = getProfileStaticProps;
export const getStaticPaths = getProfileStaticPaths;

// eslint-disable-next-line @typescript-eslint/no-unused-vars
const ProfileUpvotedPage = ({
  user,
  noindex,
}: ProfileLayoutProps): ReactElement => {
  const { user: loggedUser } = useContext(AuthContext);
  const { shouldUseListFeedLayout } = useFeedLayout();

  const isSameUser = user && loggedUser?.id === user.id;

  const userId = user?.id;
  const feedProps: FeedProps<unknown> = {
    feedName: OtherFeedPage.UserUpvoted,
    feedQueryKey: ['user_upvoted', userId],
    query: USER_UPVOTED_FEED_QUERY,
    variables: {
      userId,
    },
    disableAds: true,
    emptyScreen: isSameUser ? (
      <MyProfileEmptyScreen
        className="items-center px-4 py-6 text-center tablet:px-6"
        text="Trapped in endless meetings? Make the most of It - Find posts you love and upvote away!"
        cta="Explore posts"
        buttonProps={{ tag: 'a', href: '/' }}
      />
    ) : (
      <ProfileEmptyScreen
        title={`${user?.name ?? 'User'} hasn't upvoted yet`}
        text="Once they do, those posts will show up here."
      />
    ),
  };

  const seo: NextSeoProps = {
    ...getProfileSeoDefaults(
      user,
      {
        ...getPageSeoTitles(
          `Posts upvoted by ${user.name} (@${user.username})`,
        ),
        noindex: true,
        nofollow: true,
      },
      noindex,
    ),
  };

  return (
    <>
      <NextSeo {...seo} />
      <GoBackHeaderMobile>
        <Typography bold type={TypographyType.Body}>
          Upvoted posts
        </Typography>
      </GoBackHeaderMobile>
      <Feed
        {...feedProps}
        className={classNames('py-6', !shouldUseListFeedLayout && 'px-4')}
      />
    </>
  );
};

ProfileUpvotedPage.getLayout = getProfileLayout;
export default ProfileUpvotedPage;

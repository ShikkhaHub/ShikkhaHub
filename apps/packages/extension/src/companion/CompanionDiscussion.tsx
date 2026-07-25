import type { CSSProperties, ReactElement } from 'react';
import React from 'react';
import classNames from 'classnames';
import type { PostBootData } from '@shikkhahub/shared/src/lib/boot';
import { NewComment } from '@shikkhahub/shared/src/components/post/NewComment';
import { PostComments } from '@shikkhahub/shared/src/components/post/PostComments';
import { Origin } from '@shikkhahub/shared/src/lib/log';
import { useShareComment } from '@shikkhahub/shared/src/hooks/useShareComment';
import { useBackgroundRequest } from '@shikkhahub/shared/src/hooks/companion';
import { generateCommentsQueryKey } from '@shikkhahub/shared/src/lib/query';
import { getCompanionWrapper } from '@shikkhahub/shared/src/lib/extension';
import { ProfileImageSize } from '@shikkhahub/shared/src/components/ProfilePicture';
import CommentInputOrModal from '@shikkhahub/shared/src/components/comments/CommentInputOrModal';

interface CompanionDiscussionProps {
  post: PostBootData;
  className?: string;
  style?: CSSProperties;
  onShowUpvoted: (commentId: string, upvotes: number) => unknown;
}

export function CompanionDiscussion({
  post,
  style,
  className,
  onShowUpvoted,
}: CompanionDiscussionProps): ReactElement {
  const commentClasses = { tab: '!min-h-[14.5rem]' };
  const { openShareComment } = useShareComment(Origin.Companion);
  useBackgroundRequest(
    generateCommentsQueryKey({ postId: post?.id, sortBy: undefined }),
  );

  if (!post) {
    return null;
  }

  return (
    <div
      style={style}
      className={classNames(
        className,
        'absolute -left-px right-0 top-full flex min-h-[14rem] flex-col rounded-bl-16 bg-background-default pb-6',
      )}
    >
      <span className="px-6" />
      <div className="mt-5 flex-1 overflow-y-auto overflow-x-hidden border-t border-border-subtlest-tertiary px-4">
        <h3 className="mb-6 ml-2 mt-4 font-bold typo-callout">Discussion</h3>
        <NewComment
          size={ProfileImageSize.Medium}
          post={post}
          className={{
            ...commentClasses,
            container: 'companion-new-comment-button mb-4',
          }}
          CommentInputOrModal={CommentInputOrModal}
        />
        <PostComments
          post={post}
          origin={Origin.Companion}
          onShare={(comment) => openShareComment(comment, post)}
          onClickUpvote={onShowUpvoted}
          modalParentSelector={getCompanionWrapper}
          className={commentClasses}
        />
      </div>
    </div>
  );
}

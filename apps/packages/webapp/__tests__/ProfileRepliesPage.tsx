import React from 'react';
import type { RenderResult } from '@testing-library/react';
import { render, screen } from '@testing-library/react';
import type {
  LoggedUser,
  PublicProfile,
} from '@shikkhahub/shared/src/lib/user';
import nock from 'nock';
import { QueryClient } from '@tanstack/react-query';
import type { MockedGraphQLResponse } from '@shikkhahub/shared/__tests__/helpers/graphql';
import { mockGraphQL } from '@shikkhahub/shared/__tests__/helpers/graphql';
import { waitForNock } from '@shikkhahub/shared/__tests__/helpers/utilities';
import { TestBootProvider } from '@shikkhahub/shared/__tests__/helpers/boot';
import defaultUser from '@shikkhahub/shared/__tests__/fixture/loggedUser';
import defaultPost from '@shikkhahub/shared/__tests__/fixture/post';
import type { Connection } from '@shikkhahub/shared/src/graphql/common';
import type {
  Comment,
  UserCommentsData,
  Author,
} from '@shikkhahub/shared/src/graphql/comments';
import { USER_COMMENTS_QUERY } from '@shikkhahub/shared/src/graphql/comments';
import ProfilePage from '../pages/[userId]/replies';

beforeEach(() => {
  nock.cleanAll();
  jest.clearAllMocks();
});

const defaultProfile: PublicProfile = {
  id: 'u2',
  name: 'Daily Dev',
  username: 'shikkhahub',
  premium: false,
  reputation: 20,
  image: 'https://daily.dev/daily.png',
  cover: 'https://daily.dev/cover.png',
  bio: 'The best company!',
  createdAt: '2020-08-26T13:04:35.000Z',
  twitter: 'shikkhahub',
  github: 'shikkhahub',
  hashnode: 'shikkhahub',
  portfolio: 'https://daily.dev/?key=vaue',
  permalink: 'https://daily.dev/shikkhahub',
};

export const defaultCommentsPage: Connection<Comment> = {
  pageInfo: {
    hasNextPage: true,
    endCursor: '',
  },
  edges: [
    {
      node: {
        permalink: 'https://daily.dev/c1',
        createdAt: '2020-07-26T13:04:35.000Z',
        content: 'My comment',
        numUpvotes: 50,
        id: 'c1',
        contentHtml: 'My comment',
        post: defaultPost,
        author: defaultProfile as unknown as Author,
      },
    },
  ],
};

const createCommentsMock = (
  page = defaultCommentsPage,
): MockedGraphQLResponse<UserCommentsData> => ({
  request: {
    query: USER_COMMENTS_QUERY,
    variables: {
      userId: 'u2',
      first: 20,
      after: '',
    },
  },
  result: {
    data: {
      page,
    },
  },
});

const renderComponent = (
  mocks: MockedGraphQLResponse[] = [createCommentsMock()],
  profile: Partial<PublicProfile> = {},
  user: LoggedUser = defaultUser,
): RenderResult => {
  const client = new QueryClient();

  mocks.forEach(mockGraphQL);
  return render(
    <TestBootProvider client={client} auth={{ user }}>
      <ProfilePage user={{ ...defaultProfile, ...profile }} />
    </TestBootProvider>,
  );
};

it('should show the comments', async () => {
  renderComponent();
  await waitForNock();
  await Promise.all(
    defaultCommentsPage.edges.map(async (edge) => {
      expect(
        await screen.findByText(edge.node.contentHtml),
      ).toBeInTheDocument();
    }),
  );
});

it('should show empty screen when no posts', async () => {
  renderComponent([
    createCommentsMock({
      pageInfo: {
        hasNextPage: true,
        endCursor: '',
      },
      edges: [],
    }),
  ]);
  await waitForNock();
  const el = await screen.findByText(
    "Daily Dev hasn't replied to any post yet",
  );
  expect(el).toBeInTheDocument();
});

it('should show different empty screen when visiting your profile', async () => {
  renderComponent(
    [
      createCommentsMock({
        pageInfo: {
          hasNextPage: true,
          endCursor: '',
        },
        edges: [],
      }),
    ],
    {},
    defaultProfile as unknown as LoggedUser,
  );
  await waitForNock();
  const el = await screen.findByText('Explore posts');
  expect(el).toBeInTheDocument();
});

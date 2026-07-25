import type { FeedData } from '@shikkhahub/shared/src/graphql/posts';
import {
  ANONYMOUS_FEED_QUERY,
  RankingAlgorithm,
} from '@shikkhahub/shared/src/graphql/feed';
import nock from 'nock';
import React from 'react';
import type { RenderResult } from '@testing-library/react';
import { render, screen } from '@testing-library/react';
import { QueryClient } from '@tanstack/react-query';
import type { LoggedUser } from '@shikkhahub/shared/src/lib/user';
import type { NextRouter } from 'next/router';
import { useRouter } from 'next/router';
import ad from '@shikkhahub/shared/__tests__/fixture/ad';
import defaultUser from '@shikkhahub/shared/__tests__/fixture/loggedUser';
import defaultFeedPage from '@shikkhahub/shared/__tests__/fixture/feed';
import type { MockedGraphQLResponse } from '@shikkhahub/shared/__tests__/helpers/graphql';
import { mockGraphQL } from '@shikkhahub/shared/__tests__/helpers/graphql';
import { TestBootProvider } from '@shikkhahub/shared/__tests__/helpers/boot';
import Popular from '../pages/popular';

beforeEach(() => {
  jest.restoreAllMocks();
  jest.clearAllMocks();
  nock.cleanAll();
  jest.mocked(useRouter).mockImplementation(
    () =>
      ({
        pathname: '/popular',
        query: {},
        replace: jest.fn(),
        push: jest.fn(),
      } as unknown as NextRouter),
  );
});

const createFeedMock = (
  page = defaultFeedPage,
  query: string = ANONYMOUS_FEED_QUERY,
  variables: Record<string, unknown> = {
    first: 7,
    after: '',
    loggedIn: true,
  },
): MockedGraphQLResponse<FeedData> => ({
  request: {
    query,
    variables,
  },
  result: {
    data: {
      page,
    },
  },
});

function renderComponent(
  mocks: MockedGraphQLResponse[] = [createFeedMock()],
  user?: LoggedUser,
): RenderResult {
  const resolvedUser = arguments.length < 2 ? defaultUser : user;
  const client = new QueryClient();

  mocks.forEach(mockGraphQL);
  nock('http://localhost:3000').get('/v1/a').reply(200, [ad]);

  return render(
    <TestBootProvider client={client} auth={{ user: resolvedUser }}>
      {Popular.getLayout(<Popular />, {}, Popular.layoutProps)}
    </TestBootProvider>,
  );
}

it('should request anonymous popular feed', async () => {
  renderComponent(
    [
      createFeedMock(defaultFeedPage, ANONYMOUS_FEED_QUERY, {
        first: 7,
        after: '',
        loggedIn: false,
        version: 15,
        ranking: RankingAlgorithm.Popularity,
      }),
    ],
    undefined,
  );
  const elements = await screen.findAllByTestId('postItem');
  expect(elements.length).toBeTruthy();
});

# ShikkhaHub API Documentation

**Base URL**: `https://api.shikkhahub.com/api/v1`

## Authentication

All protected endpoints require JWT Bearer token:
```
Authorization: Bearer <access_token>
```

### Endpoints
- `POST /auth/register` - Register new user
- `POST /auth/login` - Login and get tokens
- `POST /auth/refresh` - Refresh access token
- `GET /auth/me` - Get current user

## Institutions

### List Institutions
```http
GET /institutions?page=1&page_size=20&type_id=1&division_id=2
```

### Get Institution
```http
GET /institutions/{slug}
```

## Search

### Advanced Search
```http
GET /search/advanced?q=dhaka&page=1
```

### Autocomplete
```http
GET /search/autocomplete?q=uni
```

## Reviews

### Create Review
```http
POST /reviews
Authorization: Bearer <token>
```

### List Reviews
```http
GET /institutions/{id}/reviews?sort_by=newest
```

## Admin

All admin endpoints require admin role.

- `GET /admin/dashboard/stats` - Platform statistics
- `GET /admin/institutions/pending` - Pending verifications
- `POST /admin/institutions/{id}/verify` - Verify institution
- `GET /admin/users` - List users

## SEO

- `GET /sitemap.xml` - XML sitemap
- `GET /robots.txt` - Robots file

For complete API docs, visit `/docs` when running the backend.

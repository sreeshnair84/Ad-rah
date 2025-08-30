This is a [Next.js](https://nextjs.org) project bootstrapped with [`create-next-app`](https://nextjs.org/docs/app/api-reference/cli/create-next-app).

## Getting Started

### Prerequisites
- Node.js 18+
- Backend service running (see Backend Setup below)

### Setup

First, install dependencies:

```bash
npm install
# or
yarn install
# or
pnpm install
```

Then, run the development server:

```bash
npm run dev
# or
yarn dev
# or
pnpm dev
# or
bun dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

## Backend Connection

The frontend is configured to automatically connect to the backend API running on `localhost:8000`. This is handled through Next.js rewrites in `next.config.ts`.

### Starting the Backend

For the best development experience, start the backend using Docker Compose:

```bash
cd ../backend/content_service
docker-compose up -d
```

This will start the backend with mock data pre-loaded.

### Test Accounts

Use these credentials to test the application:

- **Admin**: `admin@openkiosk.com` / `adminpass`
- **Host**: `host@openkiosk.com` / `hostpass`
- **Advertiser**: `advertiser@openkiosk.com` / `advertiserpass`

## Development

You can start editing the page by modifying `app/page.tsx`. The page auto-updates as you edit the file.

This project uses [`next/font`](https://nextjs.org/docs/app/building-your-application/optimizing/fonts) to automatically optimize and load [Geist](https://vercel.com/font), a new font family for Vercel.

## Project Structure

- `app/` - Next.js app router pages
- `components/` - Reusable UI components
- `hooks/` - Custom React hooks for API calls and state management
- `lib/` - Utility functions
- `types/` - TypeScript type definitions

## Learn More

To learn more about Next.js, take a look at the following resources:

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.

You can check out [the Next.js GitHub repository](https://github.com/vercel/next.js) - your feedback and contributions are welcome!

## Deploy on Vercel

The easiest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme) from the creators of Next.js.

Check out our [Next.js deployment documentation](https://nextjs.org/docs/app/building-your-application/deploying) for more details.

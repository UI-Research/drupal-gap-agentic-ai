import type { Core } from '@strapi/strapi';

const config = ({ env }: Core.Config.Shared.ConfigParams): Core.Config.Server => ({
  host: env('HOST', '0.0.0.0'),
  port: env.int('PORT', 1337),
  app: {
    keys: env.array('APP_KEYS'),
  },
  cron: {
    enabled: true,
    tasks: {
      // Runs every day at midnight
      '0 0 * * *': async ({ strapi }: { strapi: Core.Strapi }) => {
        const count = await strapi.documents('api::article.article').count({
          status: 'published',
        });
        strapi.log.info(`[Cron] Published articles count: ${count}`);
      },
    },
  },
});

export default config;

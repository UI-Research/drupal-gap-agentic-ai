import type { Event } from '@strapi/database/dist/lifecycles';

function generateSlug(title: string): string {
  return title
    .toLowerCase()
    .trim()
    .replace(/[^\w\s-]/g, '')
    .replace(/[\s_]+/g, '-')
    .replace(/^-+|-+$/g, '');
}

export default {
  beforeCreate(event: Event) {
    const { data } = event.params;
    if (data.title && !data.slug) {
      data.slug = generateSlug(data.title);
    }
  },

  beforeUpdate(event: Event) {
    const { data } = event.params;
    if (data.title && !data.slug) {
      data.slug = generateSlug(data.title);
    }
  },
};

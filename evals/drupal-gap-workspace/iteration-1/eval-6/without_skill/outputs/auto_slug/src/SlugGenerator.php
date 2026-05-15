<?php

declare(strict_types=1);

namespace Drupal\auto_slug;

/**
 * Service for generating URL-friendly slugs from text.
 */
class SlugGenerator {

  /**
   * Generate a URL-friendly slug from the given text.
   *
   * @param string $text
   *   The text to convert to a slug.
   *
   * @return string
   *   The generated slug.
   */
  public function generateSlug(string $text): string {
    // Convert to lowercase.
    $slug = mb_strtolower($text);

    // Replace non-alphanumeric characters with hyphens.
    $slug = preg_replace('/[^a-z0-9\-]/', '-', $slug);

    // Remove consecutive hyphens.
    $slug = preg_replace('/-+/', '-', $slug);

    // Trim hyphens from beginning and end.
    $slug = trim($slug, '-');

    return $slug;
  }

}

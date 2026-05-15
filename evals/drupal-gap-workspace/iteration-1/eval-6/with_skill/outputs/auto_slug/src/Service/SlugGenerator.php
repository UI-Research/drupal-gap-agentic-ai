<?php

namespace Drupal\auto_slug\Service;

/**
 * Service to generate URL-friendly slugs from strings.
 */
class SlugGenerator {

  /**
   * Generates a URL-friendly slug from the given string.
   *
   * @param string $string
   *   The input string (e.g., a node title).
   *
   * @return string
   *   A lowercase, hyphen-separated slug safe for URLs.
   */
  public function generateSlug(string $string): string {
    // Convert to lowercase.
    $slug = mb_strtolower($string);

    // Replace non-alphanumeric characters (except hyphens) with hyphens.
    $slug = preg_replace('/[^a-z0-9\-]/', '-', $slug);

    // Replace multiple consecutive hyphens with a single hyphen.
    $slug = preg_replace('/-+/', '-', $slug);

    // Trim hyphens from the beginning and end.
    $slug = trim($slug, '-');

    return $slug;
  }

}

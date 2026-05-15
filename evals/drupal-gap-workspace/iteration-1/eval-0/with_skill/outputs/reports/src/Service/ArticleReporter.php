<?php

namespace Drupal\reports\Service;

use Drupal\Core\Entity\EntityTypeManagerInterface;

/**
 * Service that queries published Article nodes.
 */
class ArticleReporter {

  /**
   * The node storage.
   *
   * @var \Drupal\Core\Entity\EntityStorageInterface
   */
  protected $nodeStorage;

  /**
   * Constructs an ArticleReporter object.
   *
   * @param \Drupal\Core\Entity\EntityTypeManagerInterface $entity_type_manager
   *   The entity type manager.
   */
  public function __construct(EntityTypeManagerInterface $entity_type_manager) {
    $this->nodeStorage = $entity_type_manager->getStorage('node');
  }

  /**
   * Returns an array of published Article node data.
   *
   * @return array
   *   A list of associative arrays with nid, title, and created keys.
   */
  public function getPublishedArticles(): array {
    $nids = $this->nodeStorage->getQuery()
      ->condition('type', 'article')
      ->condition('status', 1)
      ->accessCheck(TRUE)
      ->sort('created', 'DESC')
      ->execute();

    $nodes = $this->nodeStorage->loadMultiple($nids);
    $results = [];

    foreach ($nodes as $node) {
      $results[] = [
        'nid' => (int) $node->id(),
        'title' => $node->getTitle(),
        'created' => date('c', $node->getCreatedTime()),
      ];
    }

    return $results;
  }

}

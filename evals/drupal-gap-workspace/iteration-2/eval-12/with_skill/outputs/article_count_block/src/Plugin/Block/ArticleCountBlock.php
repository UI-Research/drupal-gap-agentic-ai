<?php

namespace Drupal\article_count_block\Plugin\Block;

use Drupal\Core\Block\Attribute\Block;
use Drupal\Core\Block\BlockBase;
use Drupal\Core\StringTranslation\TranslatableMarkup;

#[Block(
  id: "article_count_block",
  admin_label: new TranslatableMarkup("Article Count Block"),
  category: new TranslatableMarkup("Content"),
)]
class ArticleCountBlock extends BlockBase {

  public function build(): array {
    $count = \Drupal::entityQuery('node')
      ->condition('type', 'article')
      ->condition('status', 1)
      ->accessCheck(FALSE)
      ->count()
      ->execute();

    return [
      '#markup' => $this->t('There are @count published articles.', ['@count' => $count]),
      '#cache' => [
        'tags' => ['node_list'],
        'max-age' => 3600,
      ],
    ];
  }

}

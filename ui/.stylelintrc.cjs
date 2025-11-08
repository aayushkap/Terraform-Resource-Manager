module.exports = {
  extends: ['stylelint-config-standard-scss'],
  plugins: ['stylelint-order'],
  rules: {
    'declaration-empty-line-before': null,
    
    'order/properties-order': [
      {
        groupName: 'positioning',
        emptyLineBefore: 'always',
        properties: ['position', 'top', 'right', 'bottom', 'left', 'z-index']
      },
      {
        groupName: 'display',
        emptyLineBefore: 'always',
        properties: [
          'display', 'flex', 'flex-direction', 'flex-wrap',
          'justify-content', 'align-items', 'gap',
          'grid', 'grid-template-columns', 'grid-template-rows', 'grid-gap'
        ]
      },
      {
        groupName: 'box-model',
        emptyLineBefore: 'always',
        properties: [
          'width', 'min-width', 'max-width',
          'height', 'min-height', 'max-height',
          'margin', 'margin-top', 'margin-right', 'margin-bottom', 'margin-left',
          'padding', 'padding-top', 'padding-right', 'padding-bottom', 'padding-left'
        ]
      },
      {
        groupName: 'typography',
        emptyLineBefore: 'always',
        properties: [
          'font-family', 'font-size', 'font-weight',
          'line-height', 'letter-spacing',
          'text-align', 'text-transform', 'color'
        ]
      },
      {
        groupName: 'visual',
        emptyLineBefore: 'always',
        properties: [
          'background', 'background-color',
          'border', 'border-radius',
          'opacity', 'box-shadow'
        ]
      },
      {
        groupName: 'animation',
        emptyLineBefore: 'always',
        properties: ['transition', 'animation']
      },
      {
        groupName: 'misc',
        emptyLineBefore: 'always',
        properties: ['cursor', 'overflow', 'pointer-events']
      }
    ]
  }
};

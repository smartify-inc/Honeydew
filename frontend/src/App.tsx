import { ConfigProvider } from './config';
import { Board } from './components/Board';

function App() {
  return (
    <ConfigProvider>
      <Board />
    </ConfigProvider>
  );
}

export default App;
